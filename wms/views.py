# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.http import HttpResponse, JsonResponse
from django.core import serializers

# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import get_user_model
from web_inventory import *
from vendor.models import lens_order
from django.db import connections

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

import oms.const
from oms.models.utilities_models import utilities, DateEncoder
from util.response import response_message

from .models import *
# add by ranhy 2019-04-18
from django.db.models import Q, Count, Sum

from util.db_helper import *
from django.db import connection
from oms.models.order_models import LabOrder, PgOrder
from oms.models.order_models import laborder_request_notes, laborder_request_notes_line
from oms.models.order_models import laborder_purchase_order_line
from oms.models.ordertracking_models import OrderTracking

from oms.controllers.lab_order_controller import lab_order_controller
from api.controllers.tracking_controllers import tracking_lab_order_controller
from wms.models import inventory_struct, inventory_delivery_channel_controller, inventory_receipt_channel_controller
from oms.models.application_models import OperationLog
import time
import csv, codecs
import util
import xlrd
import logging
from wms.models import inventory_struct_contoller
from util.response import json_response, json_response_page, is_contain_chinese
from util.dict_helper import dict_helper


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


def track(id, user_entity=None, user_id=-1, user_name='system', status='', status_value='', comments=''):
    try:
        lbo = LabOrder.objects.get(lab_number=id)
        lbo.status = status
        lbo.save()
        ot = OrderTracking()
        ot.add_orderTracking(lbo.lab_number, lbo.frame, lbo.order_date, lbo, user_entity, user_name, status,
                             status_value)
    except Exception as e:
        logging.debug(e.message)


@csrf_exempt
@login_required
@permission_required('wms.DELIVERY_FRAME', login_url='/oms/forbid/')
def ajax_delivery_frame(request):
    _form_data = {}
    res = {}
    lbo = None
    wh_all = None
    _form_data['form_type'] = 'Frame'
    if request.method == 'POST':
        lab_number = request.POST.get('lab_nubmer', 'null')
        def_wh = request.POST.get('def_wh_code', '')

        if def_wh == 'null' or lab_number == '':
            res['code'] = '-1'
            res['message'] = '未选择仓库或订单号不正确'
            return JsonResponse(res)

        # 记录所选仓库
        request.session['def_wh_code'] = def_wh

        try:
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            vs = loc.verify_status(lab_number)

            # 查询镜架出库记录，若已存在一条记录，则不允许重复出库
            inde_entitys = inventory_delivery.objects.filter(lab_number=lab_number)
            if inde_entitys.count() > 0:
                res['code'] = '-1'
                res['message'] = '该订单已出过库'
                return JsonResponse(res)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            else:
                res['code'] = '-1'
                res['message'] = '请输入完整订单号或重新扫码'
                return JsonResponse(res)

            if not lbo.status == 'REQUEST_NOTES' and not lbo.status == 'LENS_RECEIVE' and not lbo.status == 'COLLECTION':
                res['code'] = '-1'
                res['message'] = '只有订单状态是出库申请或镜片收货，才能执行出库! 当前订单状态: ' + lbo.get_status_display()
                return JsonResponse(res)

            inv_struct = inventory_struct.objects.get(sku=lbo.frame)
            if inv_struct.status == 'OUT_OF_STOCK':
                res['code'] = '-1'
                res['message'] = '该【' + lbo.frame+'】处于下架状态，无法自动出库'
                return JsonResponse(res)

            doc_type = "AUTO"  # 出库类型默认为【自动出库】
            time_now = time.strftime('%Y%m%d', time.localtime(time.time()))  # 默认【当天日期】
            warehouse_code = def_wh

            inv = inventory_delivery_control()
            rm = inv.add(request, time_now, warehouse_code, lbo.frame, doc_type, lbo.quantity, '', lab_number)
            if not rm.code == 0:
                logging.debug(rm.message)
                res['code'] = '-1'
                res['message'] = rm.message
                return JsonResponse(res)
            else:
                if lbo.status == 'REQUEST_NOTES' or lbo.status == 'COLLECTION':  # 前一状态是出库申请才更新到镜架出库
                    lbo.status = 'FRAME_OUTBOUND'
                    lbo.save()

                laborder = LabOrder.objects.get(pk=lbo.id)
                action = 'FRAME_OUTBOUND'
                action_value = '镜架出库'
                tloc = tracking_lab_order_controller()
                tloc.tracking(laborder, request.user, action, action_value)

                lrn_line = laborder_request_notes_line.objects.get(lab_number=lab_number)
                lrn = lrn_line.lrn
                out_count = laborder_request_notes_line.objects.filter(lrn=lrn,
                                                                       laborder_entity__status='FRAME_OUTBOUND').count()
                _form_data['out_count'] = out_count
                _form_data['lrn'] = lrn
                _form_data['lrn_line'] = lrn_line
                _form_data['laborder'] = laborder

            return render(request, 'delivery_detail_part.html', {
                'form_data': _form_data,
                'item': lbo
            })

        except Exception as e:
            logging.debug(str(e))
            res['code'] = '-1'
            res['message'] = '数据遇到异常: ' + e
            return JsonResponse(res)


# 镜片出库AJAX
@csrf_exempt
@login_required
@permission_required('wms.DELIVERY_FRAME', login_url='/oms/forbid/')
def ajax_delivery_frame_lens(request):
    _form_data = {}
    res = {}
    lbo = None
    _form_data['form_type'] = 'Lens'
    if request.method == 'POST':
        lab_number = request.POST.get('lab_nubmer', 'null')
        def_wh = request.POST.get('def_wh_code', '')
        # 2019.10.05 暂停使用直径参数（现库存镜片同一baseSKU不存在两种直径）
        # od_diameter = request.POST.get('od_diameter', '')
        # os_diameter = request.POST.get('os_diameter', '')
        is_force = request.POST.get('is_force', 0)
        if def_wh == 'null' or lab_number == '':
            res['code'] = '-1'
            res['message'] = '未选择仓库或订单号不正确'
            return JsonResponse(res)
        # 判断是否是镜片仓库 --已在前段做约束 不再验证

        # # 判断直径是否为空
        # if not od_diameter:
        #     res['code'] = '-1'
        #     res['message'] = '请选择直径'
        #     return JsonResponse(res)
        # 记录所选镜片仓库
        request.session['def_wh_code_lens'] = def_wh

        try:
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            vs = loc.verify_status(lab_number)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            else:
                res['code'] = '-1'
                res['message'] = '请输入完整订单号或重新扫码'
                return JsonResponse(res)

            if not lbo.status == 'REQUEST_NOTES' and not lbo.status == 'PRINT_DATE' and not lbo.status == 'FRAME_OUTBOUND':
                res['code'] = '-1'
                res['message'] = '只有订单状态是出库申请、镜架出库、镜片生产，才能执行出库! 当前订单状态: ' + lbo.get_status_display()
                return JsonResponse(res)

            doc_type = "AUTO"  # 出库类型默认为【自动出库】
            time_now = time.strftime('%Y%m%d', time.localtime(time.time()))  # 默认【当天日期】
            warehouse_code = def_wh

            # 验证lens_order
            if int(is_force) == 0:
                los = lens_order.objects.filter(lab_number=lab_number)
                for lo in los:
                    if lo.status == 'LENS_OUTBOUND':
                        res['code'] = '-200'
                        res['message'] = "该订单镜片已经出库完成，若强制出库请选择强制出库"
                        return JsonResponse(res)

            # 取订单SPH判断光型
            od_luminosity_type = ''  # 右眼
            if float(lbo.od_sph) <= 0:
                od_luminosity_type = 'N'
            else:
                od_luminosity_type = 'P'
            os_luminosity_type = ''  # 左眼
            if float(lbo.os_sph) <= 0:
                os_luminosity_type = 'N'
            else:
                os_luminosity_type = 'P'

            # 根据实际镜片SKU和光型查找GUID
            od_sku = ''
            os_sku = ''
            if od_luminosity_type == os_luminosity_type:
                skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, luminosity_type=od_luminosity_type,
                                                   is_enabled=True)
                if skus.count() == 0:
                    res['code'] = '-1'
                    res['message'] = "右眼未找到对应的SKU"
                    return JsonResponse(res)
                od_sku = skus[0].sku
                os_sku = od_sku
            else:
                od_skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, luminosity_type=od_luminosity_type)
                if od_skus.count() == 0:
                    res['code'] = '-1'
                    res['message'] = "右眼未找到对应的SKU"
                    return JsonResponse(res)
                od_sku = od_skus[0].sku
                os_skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, luminosity_type=os_luminosity_type)
                if os_skus.count() == 0:
                    res['code'] = '-1'
                    res['message'] = "左眼未找到对应的SKU"
                    return JsonResponse(res)
                os_sku = os_skus[0].sku

            # # 根据实际镜片和直径获取GUID。--2019.10.05 暂停直径和base_sku获取GUID方式
            # if os_diameter == od_diameter:
            #     skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, diameter=od_diameter)
            #     if skus.count() == 0:
            #         res['code'] = '-1'
            #         res['message'] = "右眼未找到对应的SKU"
            #         return JsonResponse(res)
            #     od_sku = skus[0].sku
            #     os_sku = od_sku
            # else:
            #     od_skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, diameter=od_diameter)
            #     if od_skus.count() == 0:
            #         res['code'] = '-1'
            #         res['message'] = "右眼未找到对应的SKU"
            #         return JsonResponse(res)
            #     od_sku = od_skus[0].sku
            #     os_skus = product_lens.objects.filter(base_sku=lbo.act_lens_sku, diameter=os_diameter)
            #     if os_skus.count() == 0:
            #         res['code'] = '-1'
            #         res['message'] = "左眼未找到对应的SKU"
            #         logging.debug("od_da=" + od_diameter)
            #         logging.debug("os_da=" + os_diameter)
            #         return JsonResponse(res)
            #     os_sku = os_skus[0].sku
            #     logging.debug("od_da=" + od_diameter)
            #     logging.debug("os_da=" + os_diameter)

            # 数量验证
            isls_od = inventory_struct_lens.objects.filter(sku=od_sku, sph=lbo.od_sph, cyl=lbo.od_cyl, add=lbo.od_add)
            if isls_od.count() == 0:
                res['code'] = '-1'
                res['message'] = "右眼镜片库存信息不存在"
                return JsonResponse(res)
            else:
                isl_od = isls_od[0]
                if isl_od.quantity <= 0:
                    res['code'] = '-1'
                    res['message'] = "右眼镜片库存数量不足"
                    return JsonResponse(res)

            isls_os = inventory_struct_lens.objects.filter(sku=os_sku, sph=lbo.os_sph, cyl=lbo.os_cyl, add=lbo.os_add)
            if isls_os.count() == 0:
                res['code'] = '-1'
                res['message'] = "左眼镜片库存信息不存在"
                logging.debug('sku=' + lbo.act_lens_sku)
                return JsonResponse(res)
            else:
                isl_os = isls_os[0]
                if isl_os.quantity <= 0:
                    res['code'] = '-1'
                    res['message'] = "左眼镜片库存数量不足"
                    return JsonResponse(res)

            # 右眼出库
            # 获取镜片对象
            isl_od = isls_od[0]
            idlc = inventory_delivery_lens_controller()
            rm_od = idlc.add(request, time_now, doc_type, warehouse_code, isl_od.sku, lbo.od_sph, lbo.od_cyl,
                             lbo.od_add, lbo.quantity, '', '', lab_number)
            if not rm_od.code == 0:
                res['code'] = '-1'
                res['message'] = rm_od.message
                return JsonResponse(res)
            # 左眼出库
            # 获取镜片对象
            isl_os = isls_os[0]
            idlc = inventory_delivery_lens_controller()
            rm_os = idlc.add(request, time_now, doc_type, warehouse_code, isl_os.sku, lbo.os_sph, lbo.os_cyl,
                             lbo.os_add, lbo.quantity, '', '', lab_number)
            if not rm_os.code == 0:
                res['code'] = '-1'
                res['message'] = rm_od.message
                return JsonResponse(res)
            else:
                # 更新lab_order状态
                lbo.status = 'LENS_OUTBOUND'
                lbo.save()

                laborder = LabOrder.objects.get(pk=lbo.id)
                action = 'LENS_OUTBOUND'
                action_value = '镜片出库'
                tloc = tracking_lab_order_controller()
                tloc.tracking(laborder, request.user, action, action_value)

                # 更新lens_order状态 为LENS_OUTBOUND
                los = lens_order.objects.filter(lab_number=lab_number)
                for lo in los:
                    lo.status = 'LENS_OUTBOUND'
                    lo.save()

                lrn_line = laborder_request_notes_line.objects.get(lab_number=lab_number)
                lrn = lrn_line.lrn
                out_count = laborder_request_notes_line.objects.filter(lrn=lrn,
                                                                       laborder_entity__status='FRAME_OUTBOUND').count()
                _form_data['out_count'] = out_count
                _form_data['lrn'] = lrn
                _form_data['lrn_line'] = lrn_line
                _form_data['laborder'] = laborder

            return render(request, 'delivery_detail_part.html', {
                'form_data': _form_data,
                'item': lbo
            })

        except Exception as e:
            logging.debug('错误：' + str(e))
            res['code'] = '-1'
            res['message'] = '数据遇到异常: ' + str(e)
            return JsonResponse(res)


@csrf_exempt
@login_required
@permission_required('wms.DELIVERY_FRAME', login_url='/oms/forbid/')
def redirect_delivery_frame(request):
    _form_data = {}
    lbo = None
    wh_all = None
    _form_data['form_type'] = 'Frame'
    if request.method == 'POST':
        res = {}
        lab_number = request.POST.get('lab_nubmer', '')
        if lab_number == '':
            res['code'] = -1
            res['message'] = '请输入订单号!!'
            return JsonResponse(res)

        try:
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            else:
                res['code'] = -1
                res['message'] = '请输入完整订单号!!'
                return JsonResponse(res)

            # 用来到wms_product_frame中查找sku_specs字段（警示信息）
            caution_info = product_frame.objects.get(sku=lbo.frame)
            _form_data['caution_info'] = caution_info.sku_specs

            _form_data['laborder'] = lbo
            inv_struct = inventory_struct.objects.get(sku=lbo.frame)
            _form_data['inv_struct_status'] = inv_struct.status
            if lbo.status != '' and lbo.status is not None:
                lrn_line = laborder_request_notes_line.objects.get(lab_number=lab_number)
                lrn = lrn_line.lrn
                out_count = laborder_request_notes_line.objects.filter(lrn=lrn,
                                                                       laborder_entity__status='FRAME_OUTBOUND').count()
                _form_data['out_count'] = out_count
                _form_data['lrn'] = lrn
                _form_data['lrn_line'] = lrn_line

            return render(request, 'delivery_detail_part.html', {
                'form_data': _form_data,
                'item': lbo
            })

        except Exception as e:
            logging.debug(str(e))
            res['code'] = -1
            res['message'] = 'error'
            return JsonResponse(res)

    # GET
    # 查询仓库
    wh_all = warehouse.objects.all()
    s_def_wh = request.session.get('def_wh_code', 'null')
    _form_data['def_wh_name'] = '请选择'
    _form_data['def_wh_code'] = s_def_wh

    if not s_def_wh == 'null':
        whs = wh_all.filter(code=s_def_wh)
        if whs.count() > 0:
            _form_data['def_wh_name'] = whs[0].name

    return render(request, "delivery_frame.html", {
        'form_data': _form_data,
        'wh_all': wh_all,
    })


# 镜片出库控制
@csrf_exempt
@login_required
@permission_required('wms.DELIVERY_FRAME_LENS', login_url='/oms/forbid/')
def redirect_delivery_frame_lens(request):
    _form_data = {}
    lbo = None
    wh_all = None
    _form_data['form_type'] = 'Lens'
    if request.method == 'POST':
        res = {}
        lab_number = request.POST.get('lab_nubmer', '')
        if lab_number == '':
            res['code'] = -1
            res['message'] = '请输入订单号!!'
            return JsonResponse(res)

        try:
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            else:
                res['code'] = -1
                res['message'] = '请输入完整订单号!!'
                return JsonResponse(res)

            _form_data['laborder'] = lbo
            if lbo.status != '' and lbo.status != None:
                lrn_line = laborder_request_notes_line.objects.get(lab_number=lab_number)
                lrn = lrn_line.lrn
                out_count = laborder_request_notes_line.objects.filter(lrn=lrn,
                                                                       laborder_entity__status='FRAME_OUTBOUND').count()
                _form_data['out_count'] = out_count
                _form_data['lrn'] = lrn
                _form_data['lrn_line'] = lrn_line

            return render(request, 'delivery_detail_part.html', {
                'form_data': _form_data,
                'item': lbo
            })

        except Exception as e:
            logging.debug(str(e))
            res['code'] = -1
            res['message'] = 'Ex:' + str(e)
            return JsonResponse(res)

    # GET
    # 查询仓库
    wh_all = warehouse.objects.all()
    s_def_wh = request.session.get('def_wh_code_lens', 'null')
    _form_data['def_wh_name'] = '请选择'
    _form_data['def_wh_code'] = s_def_wh

    if not s_def_wh == 'null':
        whs = wh_all.filter(code=s_def_wh)
        if whs.count() > 0:
            _form_data['def_wh_name'] = whs[0].name

    return render(request, "delivery_frame_lens.html", {
        'form_data': _form_data,
        'wh_all': wh_all,
    })


@login_required
@permission_required('wms.INVENTORY_DELIVERY', login_url='/oms/forbid/')
def redirect_inventory_delivery(request):
    rm = {}
    # 遍历出库类型
    invd_dict = inventory_delivery_control.get_doctype_choices()
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    invds = inventory_delivery.objects.filter(doc_number=time_now).order_by("-id")
    all_wh = warehouse.objects.all()
    all_channel = channel.objects.all()

    all_products = product_frame.objects.filter(~Q(name = ''))
    # 获取页码
    page = request.GET.get('page', 1)
    # 获取URL中除page外的其它参数
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    # 分页对象，设置每页20条数据
    paginator = Paginator(invds, 20)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不在范围内，返回第一页
        contacts = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，定位最后一页
        contacts = paginator.page(paginator.num_pages)
    return render(request, "inventory_delivery.html", {
        "time_now": time_now,
        # "invds": invds,
        "invd_dict": invd_dict,
        "list": contacts,
        'paginator': paginator,
        'query_string': query_string,
        'all_wh': all_wh,
        'all_channel': all_channel,
        'all_products': all_products
    })


# 镜片手动出库
@login_required
@permission_required('wms.INVENTORY_DELIVERY_LENS', login_url='/oms/forbid/')
def redirect_inventory_delivery_lens(request):
    rm = {}
    # 遍历出库类型
    idlc_dict = inventory_delivery_lens_controller.get_doctype_choices()
    # 通过时间获取编号
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    # 获取今日入库单
    idls = inventory_delivery_lens.objects.filter(doc_number=time_now).order_by("-id")
    logging.debug(idls.query)
    # 获取所有仓库
    all_wh = warehouse.objects.all()

    # 获取所有sku
    sku_list = product_lens.objects.values('sku', 'name')
    # 获取GET参数
    doc_type = request.GET.get('doc_type', '')
    wh_code = request.GET.get('wh_code', '')
    sku = request.GET.get('sku', '')
    sph = request.GET.get('sph', '')
    cyl = request.GET.get('cyl', '')
    add = request.GET.get('add', '')
    diameter = request.GET.get('diameter', '')

    # 从数据库查询
    sph_list = None  # sph列表
    cyl_list = None  # cyl列表
    add_list = None  # add列表
    list_from = {}  # list打包
    parameter_list = {}  # parement打包
    if sku:
        parameter_list['sku'] = sku
        parameter_list['doc_type_key'] = doc_type
        parameter_list['wh_code'] = wh_code
        logging.debug("")
        sph_list = inventory_struct_lens.objects.filter(sku=sku).values('sph').distinct()

        logging.debug("sph_list_count" + str(len(sph_list)))
        list_from['sph_list'] = sph_list
        if sph:
            parameter_list['sph'] = float(sph)
            cyl_list = inventory_struct_lens.objects.filter(sku=sku, sph=float(sph)).values('cyl').distinct()
            list_from['cyl_list'] = cyl_list
            if cyl:
                parameter_list['cyl'] = float(cyl)
                add_list = inventory_struct_lens.objects.filter(sku=sku, sph=float(sph), cyl=float(cyl)).values(
                    'add').distinct()
                list_from['add_list'] = add_list
                if add:
                    parameter_list['add'] = float(add)

    # 获取页码
    page = request.GET.get('page', 1)
    # 获取URL中除page外的其它参数
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    # 分页对象，设置每页20条数据
    paginator = Paginator(idls, 20)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不在范围内，返回第一页
        contacts = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，定位最后一页
        contacts = paginator.page(paginator.num_pages)

    return render(request, "inventory_delivery_lens.html", {
        "time_now": time_now,
        # "invrs": invrs,今日入库单列表，换成传回分页对象
        "idlc_dict": idlc_dict,
        "all_wh": all_wh,
        'list': contacts,
        'paginator': paginator,
        'query_string': query_string,
        'sku_list': sku_list,  # base_sku 列表
        'list_from': list_from,
        'parameter_list': parameter_list

    })


@login_required
@permission_required('wms.INVENTORY_DELIVERY', login_url='/oms/forbid/')
def redirect_inventory_delivery_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        if request.method == 'POST':
            # 接受post过来的JSON数据
            _data = json.loads(form_data)
            # 报损出库验证必填订单号
            lab_number = _data.get('lab_number_input', '')
            if _data.get("doc_type") == 'FAULTY':
                if lab_number == '':
                    res_data['code'] = '-1'
                    res_data['error'] = "请手动输入工厂单号"
                    return JsonResponse(res_data)
            # wj 2019.06.14 去掉同步网站库存代码
            invd_ctrl = inventory_delivery_control()
            rm = invd_ctrl.add_new(request, _data)

            # rm.code 值为 0 时  查询 inventory_receipt
            # 显示当日出库全部数据  没有分页
            # 调拨出库 再添加 入库记录
            if rm.code == 0:
                if _data.get("direction") is  None or _data.get("direction") == '' or _data.get("direction") == 'None':
                    logging.debug('跳过调拨入库')
                else:
                    if _data.get("doc_type") == 'ALLOTTED_OUT':
                        invr_ctrl = inventory_receipt_control()
                        rmr = invr_ctrl.add(request, _data.get("p_number"), _data.get("direction"), _data.get("sku"), '1',
                                            'ALLOTTED_IN', _data.get("quantity"), _data.get("comments"))
                        if not rmr.code == 0:
                            res_data["code"] = -1
                            res_data["error"] = rmr.message
                            return JsonResponse(res_data)

                invds = inventory_delivery.objects.filter(doc_number=_data.get("p_number")).order_by("-id")
                invd = invds[0]
                return render(request, "inventory_delivery_item.html", {
                    "invd": invd
                })

            else:
                res_data["code"] = -1
                res_data["error"] = rm.message
                return JsonResponse(res_data)

    except Exception as e:
        logging.debug(str(e))
        res_data["code"] = -1
        res_data["error"] = "出库失败 请重试"
        return JsonResponse(res_data)


@login_required
@permission_required('wms.INVENTORY_RECEIPT', login_url='/oms/forbid/')
def redirect_inventory_receipt(request):
    rm = {}
    # 遍历入库类型
    invr_dict = inventory_receipt_control.get_doctype_choices()
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    invrs = inventory_receipt.objects.filter(doc_number=time_now).order_by("-id")
    logging.debug(invrs.query)
    all_wh = warehouse.objects.all()

    all_products = product_frame.objects.filter(~Q(name = ''))
    # 获取页码
    page = request.GET.get('page', 1)
    # 获取URL中除page外的其它参数
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    # 分页对象，设置每页20条数据
    paginator = Paginator(invrs, 20)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不在范围内，返回第一页
        contacts = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，定位最后一页
        contacts = paginator.page(paginator.num_pages)

    return render(request, "inventory_receipt.html", {
        "time_now": time_now,
        # "invrs": invrs,
        "invr_dict": invr_dict,
        "all_wh": all_wh,
        'list': contacts,
        'paginator': paginator,
        'query_string': query_string,
        'all_products': all_products
    })


# 镜片手动入库
@login_required
@permission_required('wms.INVENTORY_RECEIPT_LENS', login_url='/oms/forbid/')
def redirect_inventory_receipt_lens(request):
    rm = {}
    # 遍历入库类型
    invr_dict = inventory_receipt_lens_controller.get_doctype_choices()
    # 通过时间获取编号
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    # 获取今日入库单
    irls = inventory_receipt_lens.objects.filter(doc_number=time_now).order_by("-id")
    logging.debug(irls.query)
    # 获取所有仓库
    all_wh = warehouse.objects.all()

    # 获取所有base_sku
    sku_list = product_lens.objects.values('sku', 'name')
    # 获取GET参数
    doc_type = request.GET.get('doc_type', '')
    wh_code = request.GET.get('wh_code', '')
    sku = request.GET.get('sku', '')
    sph = request.GET.get('sph', '')
    cyl = request.GET.get('cyl', '')
    add = request.GET.get('add', '')
    diameter = request.GET.get('diameter', '')

    # 从数据库查询
    # sph_list = None  # sph列表
    # cyl_list = None  # cyl列表
    # add_list = None  # add列表
    # diameter_list = None  # diameter列表
    # list_from = {}  # list打包
    select_sph_list = []  # 入库SPH下拉列表
    parameter_list = {}  # parement打包
    if sku:
        parameter_list['sku'] = sku
        parameter_list['doc_type_key'] = doc_type
        parameter_list['wh_code'] = wh_code
        logging.debug("")
        pls = product_lens.objects.filter(sku=sku)
        pl = pls[0]
        if pl.luminosity_type == 'N':
            for i in range(-1200, 25, 25):
                select_sph_list.append(float(i) / 100)
        else:
            for i in range(0, 825, 25):
                select_sph_list.append(float(i) / 100)
        # 不能使用sku查询，否则不能查到同一base_sku下所有光度参数
        # logging.debug("sph_list_count" + str(len(diameter_list)))
        # list_from['diameter_list'] = diameter_list
        if sph:
            parameter_list['sph'] = float(sph)
            # cyl_list = inventory_struct_lens.objects.filter(base_sku=base_sku, sph=float(sph)).values('cyl').distinct()
            # list_from['cyl_list'] = cyl_list
            if cyl:
                parameter_list['cyl'] = float(cyl)
                # add_list = inventory_struct_lens.objects.filter(base_sku=base_sku, sph=float(sph),cyl=float(cyl)).values('add').distinct()
                # list_from['add_list'] = add_list
                if add:
                    parameter_list['add'] = float(add)
                    # diameter_list = inventory_struct_lens.objects.filter(base_sku=base_sku, sph=float(sph),cyl=float(cyl), add=float(add)).values('diameter').distinct()
                    # list_from['diameter_list'] = diameter_list
                    if diameter:
                        parameter_list['diameter'] = int(diameter)

    # 获取页码
    page = request.GET.get('page', 1)
    # 获取URL中除page外的其它参数
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    # 分页对象，设置每页20条数据
    paginator = Paginator(irls, 20)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不在范围内，返回第一页
        contacts = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，定位最后一页
        contacts = paginator.page(paginator.num_pages)

    return render(request, "inventory_receipt_lens.html", {
        "time_now": time_now,
        # "invrs": invrs,今日入库单列表，换成传回分页对象
        "invr_dict": invr_dict,
        "all_wh": all_wh,
        'list': contacts,
        'paginator': paginator,
        'query_string': query_string,
        'sku_list': sku_list,  # sku-name 列表
        # 'list_from': list_from,
        'parameter_list': parameter_list,
        'select_sph_list': select_sph_list

    })


@login_required
@permission_required('wms.INVENTORY_RECEIPT', login_url='/oms/forbid/')
def redirect_inventory_receipt_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        if request.method == 'POST':
            # 接受post过来的JSON数据
            _data = json.loads(form_data)
            # wj 2019.06.14 去掉同步网站库存
            invr_ctrl = inventory_receipt_control()
            rm = invr_ctrl.add(request, _data.get("p_number"), _data.get("wh_number"), _data.get("sku"),
                               _data.get("price"), _data.get("doc_type"), _data.get("quantity"), _data.get("comments"))

            # end by ranhy

            # rm.code 值为 0 时  查询 inventory_receipt
            # 显示当前入库全部数据  没有分页
            if rm.code == 0:
                invrs = inventory_receipt.objects.filter(doc_number=_data.get("p_number")).order_by("-id")
                invr = invrs[0]

                return render(request, "inventory_receipt_item.html", {
                    "invr": invr
                })
            else:
                logging.debug(rm.message)
                res_data["code"] = -1
                res_data["error"] = rm.message
                return JsonResponse(res_data)

    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "添加失败 请重试"
        logging.debug(str(e))
        return JsonResponse(res_data)


# 镜片手动入库SUBMIT
@login_required
@permission_required('wms.INVENTORY_RECEIPT_LENS', login_url='/oms/forbid/')
def redirect_inventory_receipt_lens_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        if request.method == 'POST':
            # 接受post过来的JSON数据
            _data = json.loads(form_data)
            # 解析数据
            doc_number = _data.get('doc_number')
            doc_type = _data.get('doc_type')
            warehouse_code = _data.get('wh_number')
            sku = _data.get('sku_select')
            quantity = _data.get('quantity')
            sph = _data.get('sph_select')
            cyl = _data.get('cyl_select')
            add = _data.get('add_select')
            diameter = _data.get('diameter_select')
            price = _data.get('price')
            # location =
            # entity_id =
            # 判断入库类型决定填不填写批号  ('REFUNDS_IN', '订单退货入库')
            if doc_type == 'REFUNDS_IN':
                batch_number = ''
            else:
                batch_number = ''
            comments = _data.get('comments')
            # 判断入库类型决定填不填写订单号  ('REFUNDS_IN', '订单退货入库')
            lab_number = ''
            if doc_type == 'REFUNDS_IN':
                lab_number = _data.get('lab_number_select')
                logging.debug("lab_num=" + lab_number)
                if lab_number == '':
                    res_data['code'] = '-1'
                    res_data['error'] = "请手动输入工厂单号"
                    return JsonResponse(res_data)
            # 判断仓库类型--已在前段做约束 不再验证

            # 验证product_lens ，以后镜片参数增多，在这里加参数匹配
            skus = product_lens.objects.filter(sku=sku)
            if skus.count() == 0:
                res_data['code'] = '-1'
                res_data['error'] = "未找到对应的镜片"
                logging.debug("sku=" + sku)
                logging.debug("diameter=" + diameter)
                return JsonResponse(res_data)

            # 不做库存验证，没有则新建
            # isls = inventory_struct_lens_batch.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add)
            # if isls.count() == 0:
            #    res_data['code'] = '-1'
            #    res_data['error'] = "镜片库存信息不存在"
            #   return JsonResponse(res_data)

            # 写入
            irlc = inventory_receipt_lens_controller()
            rm = irlc.add(request, doc_number, doc_type, warehouse_code, sku, quantity, sph, cyl, add, price, '', '',
                          batch_number, comments, lab_number)

            # rm.code 值为 0 时  查询 inventory_receipt_lens
            # 显示当前入库全部数据  没有分页
            if rm.code == 0:
                irls = inventory_receipt_lens.objects.filter(doc_number=_data.get("doc_number")).order_by("-id")
                irl = irls[0]

                return render(request, "inventory_receipt_lens_item.html", {
                    "invr": irl
                })
            else:
                logging.debug(rm.message)
                res_data["code"] = -1
                res_data["error"] = rm.message
                return JsonResponse(res_data)

    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "添加失败 请重试:" + str(e)
        return JsonResponse(res_data)


# 镜片手动出库SUBMIT
@login_required
@permission_required('wms.INVENTORY_DELIVERY_LENS', login_url='/oms/forbid/')
def redirect_inventory_delivery_lens_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        if request.method == 'POST':
            # 接受post过来的JSON数据
            _data = json.loads(form_data)
            # 解析数据
            doc_number = _data.get('doc_number')
            doc_type = _data.get('doc_type')
            warehouse_code = _data.get('wh_number')
            sku = _data.get('sku_select')
            quantity = _data.get('quantity')
            sph = _data.get('sph_select')
            cyl = _data.get('cyl_select')
            add = _data.get('add_select')
            diameter = _data.get('diameter_select')
            price = _data.get('price')
            # location =
            # entity_id =
            batch_number = ''
            comments = _data.get('comments')
            # 判断出库类型决定填不填写订单号  ('FAULTY', '报损出库')
            lab_number = _data.get('lab_number_select')
            if doc_type == 'FAULTY':
                if lab_number == '':
                    res_data['code'] = '-1'
                    res_data['error'] = "请手动输入工厂单号"
                    return JsonResponse(res_data)
            # 判断出库类型决定填不填写批号  ('REFUNDS_IN', '订单退货入库')
            if doc_type == 'REFUNDS_IN':
                batch_number = ''
            else:
                batch_number = ''
            # 以后镜片参数增多，在这里加参数匹配
            skus = product_lens.objects.filter(sku=sku)
            if skus.count() == 0:
                res_data['code'] = '-1'
                res_data['error'] = "未找到对应的SKU"
                logging.debug("base_sku=" + sku)
                logging.debug("diameter=" + diameter)
                return JsonResponse(res_data)
            # 数量验证
            isls = inventory_struct_lens.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add)
            if isls.count() == 0:
                res_data['code'] = '-1'
                res_data['error'] = "镜片库存信息不存在"
                return JsonResponse(res_data)
            else:
                isl = isls[0]
                if isl.quantity - int(quantity) < 0:  # 可以在此设置警戒库存,目前可以出至0片
                    res_data['code'] = '-1'
                    res_data['error'] = "镜片库存数量不足"
                    return JsonResponse(res_data)
            # 必须保证product_lens和镜片库的一致性
            # 写入
            irlc = inventory_delivery_lens_controller()
            rm = irlc.add(request, doc_number, doc_type, warehouse_code, sku, sph, cyl, add, quantity, batch_number,
                          comments, lab_number)

            # rm.code 值为 0 时  查询 inventory_receipt_lens
            # 显示当前入库全部数据 没有分页
            if rm.code == 0:
                # 获取今日入库单
                idls = inventory_delivery_lens.objects.filter(doc_number=doc_number).order_by("-id")
                idl = idls[0]
                logging.debug(idls.query)

                return render(request, "inventory_delivery_lens_item.html", {
                    "invd": idl
                })
            else:
                logging.debug(rm.message)
                res_data["code"] = -1
                res_data["error"] = rm.message
                return JsonResponse(res_data)

    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "添加失败 请重试:" + str(e)
        return JsonResponse(res_data)

@login_required
@permission_required('wms.INVENTORY_STRUCT', login_url='/oms/forbid/')
def redirect_inventory_struct(request):
    _form_data = {}
    _items = []
    _rm = response_message()
    _rm.code = 0
    is_dr = False

    page = request.GET.get('page', 1)
    currentPage = int(page)
    _sku = request.GET.get('sku', '')
    _filter = request.GET.get('filter', 'all')
    _flatrate = request.GET.get('flatrate', 'all')
    location = request.GET.get('location', '')
    warehouse_code = request.GET.get('warehouse_code', '')

    try:
        lbo = None
        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')
            _sku = request.POST.get('sku', '')
            location = request.POST.get('location', '')
            warehouse_code = request.POST.get('warehouse_code', '')

            if lab_number == '':
                res['code'] = -1
                res['message'] = '请输入订单号!!'
                return HttpResponse(json.dumps(res))
            try:

                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_number)

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]

            except Exception as e:
                res['code'] = -999
                res['message'] = '数据遇到异常: ' + e.message

            return HttpResponse(json.dumps(res))

        _filter_doctors = customer_flatrate.objects.all()

        if not _sku == '':
            ists = inventory_struct.objects.filter(sku=_sku)
            if len(ists) == 0:
                ists = inventory_struct.objects.filter(name__contains=_sku)
        elif _filter == 'all':
            ists = inventory_struct.objects.all().exclude(retired=True)
        else:
            # retired目前作为filter中的一项来处理
            if _filter.lower() == 'retired':
                ists = inventory_struct.objects.filter(retired=True)
            else:
                ists = inventory_struct.objects.filter(status=_filter.upper()).exclude(retired=True)

        if _flatrate == 'all':
            pass
        else:
            is_dr = True
            frames = product_frame.objects.filter(flatrate_customers=_flatrate)
            frames_list = []
            for frame in frames:
                frames_list.append(frame.sku)
                logging.debug(frame.sku)
            ists = inventory_struct.objects.filter(sku__in=frames_list)

        # 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _items = ists.order_by('quantity')

        _form_data['total'] = len(_items)

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_struct.html", {
            'form_data': _form_data,
            'list': _items,
            'filter': _filter,
            'filter_doctors': _filter_doctors,
            'response_message': _rm,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': reverse('wms_inventory_struct'),
            'flatrate': _flatrate,
            'is_dr': is_dr,
            'query_string': query_string,
            'sku':_sku,
            'location':location,
            'warehouse_code':warehouse_code,
        })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'Frame Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_struct'),
        })
@login_required
@permission_required('wms.INVENTORY_STRUCT', login_url='/oms/forbid/')
def redirect_inventory_struct_warehouse(request):
    _form_data = {}
    _items = []
    _rm = response_message()
    _rm.code = 0
    is_dr = False

    page = request.GET.get('page', 1)
    currentPage = int(page)
    _sku = request.GET.get('sku', '')
    _filter = request.GET.get('filter', 'all')
    try:
        wc = warehouse_controller()
        _form_data['warehouse_list'] = wc.get_all_frame_warehouse()
        with connections['pg_oms_query'].cursor() as cursor:
            sql = '''SELECT
                        t0.id,
                        t0.sku,
                        t1.`name`,
                        t0.quantity,
                        t0.warehouse_code,
                        t0.warehouse_name,
                        t0.location,
                        t2.`status`
                    FROM
                        wms_inventory_struct_warehouse AS t0
                    LEFT JOIN wms_product_frame AS t1 ON t0.sku = t1.sku
                    LEFT JOIN wms_inventory_struct AS t2 ON t0.sku = t2.sku '''
            if not _sku == '':
                sql = sql + ''' WHERE t0.sku LIKE "%%%s%%" ORDER BY t0.sku''' % _sku
            elif  _filter == 'all':
                sql = sql + ''' ORDER BY t0.sku '''
            else:
                sql = sql + ''' WHERE t0.warehouse_code="%s" ORDER BY t0.sku''' % _filter.upper()
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)
        _form_data['total'] = len(_items)
        # 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_struct_warehouse.html",
                      {
                          'form_data': _form_data,
                          'list': _items,
                          'filter': _filter,
                          'response_message': _rm,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': reverse('wms_inventory_struct_warehouse'),
                          'query_string': query_string,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'Frame Delivery'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('wms_inventory_struct_warehouse'),
                      })


@login_required
@permission_required('wms.INVENTORY_STRUCT', login_url='/oms/forbid/')
def redirect_inventory_struct_warehouse_csv(request):
    _form_data = {}
    _items = []
    _rm = response_message()
    _rm.code = 0
    is_dr = False

    page = request.GET.get('page', 1)
    currentPage = int(page)
    _sku = request.GET.get('sku', '')
    _filter = request.GET.get('filter', 'all')
    try:
        wc = warehouse_controller()
        _form_data['warehouse_list'] = wc.get_all_frame_warehouse()

        with connections['pg_oms_query'].cursor() as cursor:
            sql = '''SELECT
                        t0.id,
                        t0.sku,
                        t1.`name`,
                        t0.quantity,
                        t0.warehouse_code,
                        t0.warehouse_name,
                        t0.location,
                        t2.`status`
                    FROM
                        wms_inventory_struct_warehouse AS t0
                    LEFT JOIN wms_product_frame AS t1 ON t0.sku = t1.sku
                    LEFT JOIN wms_inventory_struct AS t2 ON t0.sku = t2.sku '''
            if not _sku == '':
                sql = sql + ''' WHERE t0.sku LIKE "%%%s%%" ORDER BY t0.sku''' % _sku
            elif  _filter == 'all':
                sql = sql + ''' ORDER BY t0.sku '''
            else:
                sql = sql + ''' WHERE t0.warehouse_code="%s" ORDER BY t0.sku''' % _filter.upper()
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)
            _form_data['total'] = len(_items)

        data_list = []
        for item in _items:
            data_list.append({
                "id":item.id,
                "sku":item.sku,
                "name": item.name,
                "quantity":item.quantity,
                "warehouse_code":item.warehouse_code,
                "warehouse_name":item.warehouse_name,
                "location":item.location,
                "get_status":item.status
            })

        import csv, codecs

        response = HttpResponse(content_type='text/csv')
        file_name = 'wms_inventory_struct_warehouse'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            'ID', 'SKU', '名称', '数量', '代码', '仓库', '货位', '在售状态'
        ])

        for item in data_list:
            writer.writerow([
                item['id'],
                item['sku'],
                item['name'],
                item['quantity'],
                item['warehouse_code'],
                item['warehouse_name'],
                item['location'],
                item['get_status']
            ])

        return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
@permission_required('wms.INVENTORY_STRUCT', login_url='/oms/forbid/')
def redirect_inventory_struct_warehouse_location(request):
    '''
    基于仓库的货位管理
    :param request:
    :return:
    '''
    _form_data = {}
    _items = []
    _rm = response_message()
    _rm.code = 0
    is_dr = False

    page = request.GET.get('page', 1)
    currentPage = int(page)
    _sku = request.GET.get('sku', '')
    _filter = request.GET.get('filter', 'all')

    try:
        wc = warehouse_controller()
        _form_data['warehouse_list'] = wc.get_all_frame_warehouse()

        if not _sku == '':
            ists = inventory_struct_warehouse.objects.filter(sku=_sku)
            if len(ists) == 0:
                ists = inventory_struct_warehouse.objects.filter(sku__contains=_sku)
        elif _filter == 'all':
            ists = inventory_struct_warehouse.objects.all()
        else:
            ists = inventory_struct_warehouse.objects.filter(warehouse_code=_filter.upper())

        _items = ists.order_by('sku')
        _form_data['total'] = _items.count()

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_struct_warehouse_location.html",
                      {
                          'form_data': _form_data,
                          'list': _items,
                          'filter': _filter,
                          'response_message': _rm,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('wms_inventory_struct_warehouse_location'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'Frame Delivery'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('wms_inventory_struct_warehouse_location'),
                      })


# 镜片仓库报告--按批号显示也在此
@login_required
@permission_required('wms.INVENTORY_STRUCT_LENS', login_url='/oms/forbid/')
def redirect_inventory_struct_lens(request):
    _form_data = {}  # 回传参数
    _items = None  # 回传列表
    rm = response_message()

    page = request.GET.get('page', 1)
    _sku = request.GET.get('sku', '')

    try:
        # 按条件搜索
        where = 'where pl.is_enabled = TRUE'
        if _sku:
            where = 'where base_sku = "%s"' % _sku
        # 获取镜片库存表
        with connections['pg_oms_query'].cursor() as cursor:
            week_sql = '''
                select pl.is_enabled,pl.base_sku,pl.sku,pl.`name`,pl.index,pl.luminosity_type,pl.diameter,pl.vendor_name,sum(isl.quantity) as sum
                FROM wms_inventory_struct_lens as isl LEFT JOIN wms_product_lens as pl
                ON isl.sku = pl.sku
                %s
                GROUP BY isl.sku
                ORDER BY pl.index,pl.base_sku,pl.luminosity_type

            ''' % where
            cursor.execute(week_sql)
            _items = namedtuplefetchall(cursor)

        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = len(_items)

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_struct_lens.html", {
            'form_data': _form_data,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_struct_lens'),
            'list': _items,
            'query_string': query_string,
            'paginator': paginator,
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Frame Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_struct_lens'),
        })


# 镜片仓库结构详情
@login_required
@permission_required('wms.INVENTORY_STRUCT_LENS', login_url='/oms/forbid/')
def redirect_inventory_struct_lens_detail(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()

    page = request.GET.get('page', 1)
    _sku = request.GET.get('sku', '')
    _batch_number = request.GET.get('batch_number', 'all')
    _wh_code = request.GET.get('wh_code', 'all')

    logging.debug('sku=%s' % _sku)

    try:
        # 打包上面获取的参数
        _form_data['sku'] = _sku
        _form_data['batch_number'] = _batch_number
        _form_data['wh_code'] = _wh_code
        # 获取仓库列表
        wh_list = warehouse_controller().get_all_frame_warehouse()
        _form_data['wh_list'] = wh_list
        # 获取批号列表
        batch_number_list = inventory_struct_lens_batch.objects.values('batch_number').order_by(
            'batch_number').distinct()
        _form_data['batch_number_list'] = batch_number_list
        # 生成光度列表
        cyl_list = []
        sph_list_h = []  # 近视
        sph_list_p = []  # 老花
        for i in range(0, -1225, -25):
            sph_list_h.append(float(i) / 100)
        for i in range(25, 825, 25):
            sph_list_p.append(float(i) / 100)
        for i in range(0, -625, -25):
            cyl_list.append(float(i) / 100)
        _form_data['cyl_list'] = cyl_list
        # _form_data['sph_list'] = sph_list
        # 获取库存数量
        if _batch_number == 'all' and _wh_code == 'all':
            logging.debug('获取全部')
            _items = inventory_struct_lens.objects.filter(sku=_sku)
            if _items.count() == 0:
                logging.debug('sku信息错误')
                rm.code = -1
                rm.message = 'sku信息错误'
                _items = []
                raise Exception('sku信息错误')
            logging.debug('列表数量=%s' % _items.count())
        else:
            if _batch_number == 'all':
                logging.debug('筛选仓库')
                with connections["pg_oms_query"].cursor() as cursor:
                    sql = '''
                        SELECT name,sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and sku='%s'
                        GROUP BY sph,cyl
                    ''' % (_wh_code, _sku)
                    cursor.execute(sql)
                    results = namedtuplefetchall(cursor)
                    for r in range(len(results)):
                        _items.append(results[r])
                if len(_items) == 0:
                    logging.debug('sku与仓库不匹配')
                    rm.code = -1
                    rm.message = 'sku信息错误'
                    _items = []
                    raise Exception('仓库' + _wh_code + '不存在该种镜片')
                logging.debug('列表数量=%s' % len(_items))
            elif _wh_code == 'all':
                logging.debug('筛选批次')
                with connections["pg_oms_query"].cursor() as cursor:
                    sql = '''
                        SELECT name,sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where batch_number = '%s' and sku='%s'
                        GROUP BY sph,cyl
                    ''' % (_batch_number, _sku)
                    cursor.execute(sql)
                    results = namedtuplefetchall(cursor)
                    for r in range(len(results)):
                        _items.append(results[r])
                if len(_items) == 0:
                    logging.debug('sku信息错误')
                    rm.code = -1
                    rm.message = 'sku信息错误'
                    _items = []
                    raise Exception('第' + str(_batch_number) + '批次不存在该种镜片')
                logging.debug('列表数量=%s' % len(_items))
            else:
                logging.debug('筛选批次和仓库')
                _items = inventory_struct_lens_batch.objects.filter(sku=_sku, batch_number=_batch_number,
                                                                    warehouse_code=_wh_code)
                if _items.count() == 0:
                    logging.debug('sku信息错误')
                    rm.code = -1
                    rm.message = 'sku信息错误'
                    _items = []
                    raise Exception('仓库' + _wh_code + '第' + str(_batch_number) + '批次不存在该种镜片')
                logging.debug('列表数量=%s' % _items.count())
        # 取出第一条的名字
        list_one = _items[0]
        _form_data['list_one'] = list_one
        # 取出数量，包装成数组
        quantity_lisy = []
        for s in sph_list_h:  # 封装近视数据
            quantity_lisy_part = []
            insert_index = 0
            for c in cyl_list:
                quantity_lisy_values = 0
                for g in _items:
                    if g.sph == s and g.cyl == c:
                        quantity_lisy_values = g.quantity
                        if quantity_lisy_values > 0:
                            insert_index = 1
                        break
                quantity_lisy_part.append(quantity_lisy_values)
            if insert_index:
                quantity_lisy_part.insert(0, str(s))
                quantity_lisy.append(quantity_lisy_part)

        for s in sph_list_p:  # 封装老花
            quantity_lisy_part = []
            insert_index = 0
            for c in cyl_list:
                quantity_lisy_values = 0
                for g in _items:
                    if g.sph == s and g.cyl == c:
                        quantity_lisy_values = g.quantity
                        if quantity_lisy_values > 0:
                            insert_index = 1
                        break
                quantity_lisy_part.append(quantity_lisy_values)
            if insert_index:
                quantity_lisy_part.insert(0, str(s))
                quantity_lisy.append(quantity_lisy_part)

        _form_data['quantity_list'] = quantity_lisy
        _form_data['total'] = len(_items)

        return render(request, "inventory_struct_lens_detail.html", {
            'form_data': _form_data,
            'list': _items,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_struct_lens_detail'),
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_struct_lens_detail'),
        })


# 镜片仓库数量校准-上传EXCEL
@login_required
@permission_required('wms.INVENTORY_STRUCT_LENS_CALIBRATION', login_url='/oms/forbid/')
def inventory_struct_lens_calibration_upload_excel(request):
    logging.debug('进入上传VIEW')
    if request.method == "POST":  # 请求方法为POST时，进行处理
        try:
            file_obj = request.FILES.get("file")
            name = file_obj.name
            f_write = open(name, "wb")
            for line in file_obj:
                f_write.write(line)
            return JsonResponse({'code': 0, 'message': name})
        except Exception as e:
            return JsonResponse({'code': -1, 'message': str(e)})


# 镜片仓库数量校准
@login_required
@permission_required('wms.INVENTORY_STRUCT_LENS_CALIBRATION', login_url='/oms/forbid/')
def inventory_struct_lens_calibration(request):
    logging.debug('开始库存校准程序')
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    cyl_list = []  # 光度列表
    sph_list = []  # 光度列表
    rm = response_message()
    # 获得GET参数
    _sku = request.GET.get('sku', '')
    _file_name = request.GET.get('file_name', '')
    _batch_number = request.GET.get('batch_number', 'all')
    _wh_code = request.GET.get('wh_code', 'all')
    _form_data['sku'] = _sku
    _form_data['file_name'] = _file_name
    _form_data['batch_number'] = _batch_number
    _form_data['wh_code'] = _wh_code
    logging.debug('wh_code=%s' % _wh_code)
    logging.debug('file_name=%s' % _file_name)
    try:
        logging.debug('开始读取EXCEL')
        # 获取excel对象
        exl = xlrd.open_workbook(_file_name)
        # 获取第一张表
        sheet = exl.sheet_by_index(0)
        # 获取sku
        sku = sheet.cell_value(2, 1)  # excel表中是3行B列
        if not sku == _sku:
            raise Exception('Excel中SKU与所选镜片库存不相符')
        logging.critical('sku=%s' % sku)
        # 获取最大行和列
        max_row = sheet.nrows
        max_col = sheet.ncols
        # 获取 sph cyl 列表
        excel_cyl_list = sheet.row_values(6)  # 第6行
        excel_sph_list = sheet.col_values(0)  # 第0列
        # 二重字典存储 数量
        excel_quantity_list = {}
        # 循环遍历数量,并写入初始化表
        for row in range(7, max_row - 3):
            sph = excel_sph_list[row]  # 第3列的第row行
            excel_quantity_list[sph] = {}
            for col in range(1, max_col):
                cyl = excel_cyl_list[col]  # 第2行的第col列
                quantity = sheet.cell_value(row, col)
                excel_quantity_list[sph][cyl] = quantity
                # 暂时存入二维数组
        logging.critical("读取Excel操作完成,%s" % rm.message)
        # 读取库存
        logging.debug('获取指定SKU的库存信息')
        # 生成光度列表
        cyl_list = []
        sph_list = []
        for i in range(-1200, 825, 25):
            sph_list.append(float(i) / 100)
        for i in range(0, -625, -25):
            cyl_list.append(float(i) / 100)
        _form_data['cyl_list'] = cyl_list
        _form_data['sph_list'] = sph_list
        # 获取库存数量
        with connections["pg_oms_query"].cursor() as cursor:
            sql = '''
                SELECT name,sku,sph,cyl,sum(quantity) quantity
                FROM wms_inventory_struct_lens_batch 
                where warehouse_code = '%s' and sku='%s'
                GROUP BY sph,cyl
            ''' % (_wh_code, _sku)
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            for r in range(len(results)):
                _items.append(results[r])
        # 取出第一条的名字
        list_one = _items[0]
        _form_data['list_one'] = list_one
        # 取出数量，包装成数组
        quantity_lisy = []
        # 计算出的出入库差值存储起来，根据它出入库
        excel_diff_list = []
        for s in sph_list:
            quantity_lisy_part = []
            insert_index = 0  # 可以添加到列表标志
            for c in cyl_list:
                quantity_lisy_values = 0
                excel_quantity = ''
                try:
                    excel_quantity = excel_quantity_list[s][c]
                except Exception as e:
                    pass
                if excel_quantity == '':  # excel中没有数据
                    for g in _items:
                        if g.sph == s and g.cyl == c:
                            quantity_lisy_values = g.quantity
                            if quantity_lisy_values > 0:
                                insert_index = 1
                            break
                    quantity_lisy_part.append(quantity_lisy_values)
                else:  # excel中有数据
                    for g in _items:  # 遍历库存
                        if g.sph == s and g.cyl == c:  # 库存中存在该光度记录
                            quantity_lisy_values = g.quantity
                            diff = int(excel_quantity) - int(quantity_lisy_values)
                            diff = int(diff)
                            if not diff == 0:  # excel与库存有差异
                                if diff > 0:
                                    quantity_lisy_values = str(g.quantity) + '+' + str(diff) + '=' + str(
                                        int(g.quantity) + diff)
                                else:
                                    quantity_lisy_values = str(g.quantity) + str(diff) + '=' + str(
                                        int(g.quantity) + diff)
                                excel_diff_list.append({'sph': s, 'cyl': c, 'diff': diff})  # 存入列表
                            insert_index = 1
                    if not insert_index:  # 库存中不存在该光度记录
                        excel_quantity = int(excel_quantity)
                        quantity_lisy_values = '0' + '+' + str(excel_quantity) + '=' + str(excel_quantity)
                        excel_diff_list.append({'sph': s, 'cyl': c, 'diff': excel_quantity})  # 存入列表
                        insert_index = 1
                    quantity_lisy_part.append(quantity_lisy_values)
            if insert_index:
                quantity_lisy_part.insert(0, str(s))
                quantity_lisy.append(quantity_lisy_part)
        logging.debug('list=%s' % excel_diff_list)
        _form_data['quantity_list'] = quantity_lisy
        _form_data['total'] = len(_items)
        return render(request, "inventory_struct_lens_calibration.html", {
            'form_data': _form_data,
            'list': _items,
            'excel_diff_list': excel_diff_list,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_struct_lens_calibration'),
        })
    except Exception as e:
        logging.debug('Exception: ' + str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Calibration'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_struct_lens_calibration'),
        })


# 镜片仓库数量校准-出入库
@login_required
@permission_required('wms.INVENTORY_STRUCT_LENS_CALIBRATION', login_url='/oms/forbid/')
def inventory_struct_lens_calibration_do(request):
    try:
        if request.method == "POST":
            rm = response_message()
            json_excel_quantity_list = request.POST.get('excel_list', '')
            sku = request.POST.get('sku', '')
            # batch_number = request.POST.get('batch_number', '')
            wh_code = request.POST.get('wh_code', '')
            eavl_list = eval(json_excel_quantity_list)
            logging.debug('sku=%s' % sku)
            logging.debug('wh_code=%s' % wh_code)
            # 生成DOC_number
            time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
            for item in eavl_list:
                rm_p = response_message()
                # 已经是和现有库存比对出来的结果所以不做负库存验证
                if item['diff'] > 0:  # 入库
                    sph = item['sph']
                    cyl = item['cyl']
                    add = 0
                    quantity = item['diff']
                    irlc = inventory_receipt_lens_controller()
                    rm_p = irlc.add(request, time_now, 'STOCK_TAKING', wh_code, sku, quantity, sph, cyl, add, 0, '', '',
                                    '', '批量库存差异调整', '')
                elif item['diff'] < 0:  # 出库
                    sph = item['sph']
                    cyl = item['cyl']
                    add = 0
                    quantity = -item['diff']
                    idlc = inventory_delivery_lens_controller()
                    rm_p = idlc.add(request, time_now, 'STOCK_TAKING', wh_code, sku, sph, cyl, add, quantity, '',
                                    '批量库存差异调整', '')
                else:
                    rm_p.code = -1
                    rm_p.message = '差异为0不做调整'

                if not rm_p.code == 0:
                    rm.code = rm_p.code
                    rm.message += '|' + 'SPH=' + str(item['sph']) + ',' + 'CYL=' + str(
                        item['cyl']) + ',' + 'DIFF=' + str(item['diff']) + ',(' + rm_p.message + ')---------'
            return JsonResponse({'code': rm.code, 'message': rm.message})
    except Exception as e:
        logging.debug('Exceptions:%s' % str(e))
        return JsonResponse({'code': -1, 'message': str(e)})


@login_required
@permission_required('wms.REPLENISHMENT', login_url='/oms/forbid/')
def update_estimate_replenishment_date(request):
    item_id = request.POST.get('item_id', '')
    tar_time = request.POST.get('tar_time', '')
    rm = util.response.response_message()

    data_list = (item_id, tar_time)
    if not '' in data_list:
        try:
            ins = inventory_struct.objects.get(pk=item_id)
            wi = web_inventory()
            is_s = wi.update_web_struct_info({'sku': ins.sku, 'expected_delivery': tar_time})
            if not is_s:
                raise Exception('库存接口异常.')
            ins.estimate_replenishment_date = tar_time
            ins.save()
            rm.obj = {'tar_time': tar_time}
        except Exception as e:
            rm.capture_execption(e)
            return JsonResponse({'code': rm.code, 'message': rm.message})

    else:
        rm.code = -1
        rm.message = 'time or id is None'
        return JsonResponse({'code': rm.code, 'message': rm.message})

    return JsonResponse({'code': rm.code, 'obj': rm.obj})


@login_required
@permission_required('wms.RETIRED', login_url='/oms/forbid/')
def edit_retired(request):
    frame_sku = request.POST.get('frame')
    is_ret = request.POST.get('is_ret')
    reason = request.POST.get('reason')
    rm = util.response.response_message.response_dict()

    try:
        wi = web_inventory()
        invs = inventory_struct.objects.get(sku=frame_sku)
        action_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if is_ret == 'true':
            is_s = wi.update_web_struct_info({'sku': frame_sku, 'retired': True})
            if not is_s:
                raise Exception('库存接口异常.')
            invs.retired = True
            invs.last_retired = reason
            invs.last_retired_date = action_time
            rm['message'] = 'True'
        elif is_ret == 'false':
            is_s = wi.update_web_struct_info({'sku': frame_sku, 'retired': False})
            if not is_s:
                raise Exception('库存接口异常.')
            invs.retired = False
            invs.last_retired = reason
            invs.last_retired_date = action_time
            rm['message'] = 'False'
        else:
            rm['code'] = '-1'
            rm['message'] = 'ERR==> is_ret:%s, frame_sku:%s' % (is_ret, frame_sku)
            return JsonResponse(rm)

        invs.save()
        # OperationLog log
        ol = OperationLog()
        ol.log(invs.type, invs.id, invs.retired, "retired", request.user, comments=reason)
        # 日志存到inventory_operation_log
        ol = inventory_operation_log()
        ol.log(frame_sku, reason, 'retired', request.user)

    except Exception as e:
        rm['code'] = '-1'
        rm['message'] = str(e)

    return JsonResponse(rm)


@login_required
@permission_required('wms.RETIRED', login_url='/oms/forbid/')
def edit_lock_quantity(request):
    frame_sku = request.POST.get('frame', '')
    lock_quantity = request.POST.get('lock_quantity', '')
    rm = util.response.response_message.response_dict()

    try:
        # wi = web_inventory()
        invs = inventory_struct.objects.get(sku=frame_sku)
        if lock_quantity != '':
            # is_s = wi.update_web_struct_info({'sku': frame_sku, 'lock_quantity': int(lock_quantity)})
            # if not is_s:
            #    raise Exception('库存接口异常.')

            invs.lock_quantity = int(lock_quantity)
            rm['message'] = lock_quantity
        else:
            rm['code'] = '-1'
            rm['message'] = 'ERR==> lock_quantity:%s, frame_sku:%s' % (lock_quantity, frame_sku)
            return JsonResponse(rm)

        invs.save()
        # OperationLog log
        ol = OperationLog()
        ol.log(invs.type, invs.id, invs.lock_quantity, "lock_quantity", request.user)

    except Exception as e:
        rm['code'] = '-1'
        rm['message'] = str(e).encode('raw_unicode_escape')

    return JsonResponse(rm)


@login_required
@permission_required('wms.RETIRED', login_url='/oms/forbid/')
def edit_stock(request):
    frame_sku = request.POST.get('frame')
    reason = request.POST.get('reason')
    stock = request.POST.get('stock')
    rm = util.response.response_message.response_dict()
    try:
        if 'OUT_OF_STOCK' == stock or 'IN_STOCK' == stock:
            wi = web_inventory()
            stock_response = wi.update_web_struct_info({'sku': frame_sku, 'status': stock})
            if not stock_response:
                raise Exception('库存接口异常.')
        invs = inventory_struct.objects.get(sku=frame_sku)
        # inventory_struct.objects.filter(sku=frame_sku).update(status=stock)
        action_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if 'OUT_OF_STOCK' == stock:
            invs.status = stock
            invs.last_out_of_stock = reason
            invs.last_out_of_stock_date = action_time
        if 'IN_STOCK' == stock:
            invs.status = stock
            invs.last_in_stock = reason
            invs.last_in_stock_date = action_time
        if 'SIGN' == stock:
            invs.last_sign = reason
            invs.last_sign_date=action_time
        invs.save()
        ol = inventory_operation_log()
        ol.log(frame_sku, reason, stock, request.user)
        rm['code'] = '0'
        rm['message'] = stock
        return JsonResponse(rm)
    except Exception as e:
        rm['code'] = '-1'
        rm['message'] = str(e).encode('raw_unicode_escape').decode('unicode-escape').encode('utf-8')

    return JsonResponse(rm)


# 镜架入库记录报告
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_receipt_report(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 通过时间获取编号
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    _form_data['time_now'] = time_now
    # 获取GET参数
    page = request.GET.get('page', 1)
    doc_number = request.GET.get('doc_number', '')
    _form_data['doc_number'] = doc_number
    sku = request.GET.get('sku', '')
    _form_data['sku'] = sku
    wh_code = request.GET.get('wh_code', '0')
    wh_code = int(wh_code)  # 镜架入库表存储的是仓库ID
    _form_data['wh_code'] = wh_code
    doc_type = request.GET.get('doc_type', '')
    _form_data['doc_type'] = doc_type
    user = request.GET.get('user', '')
    _form_data['user'] = user
    start_time = request.GET.get('start_time', '')
    _form_data['start_time'] = start_time
    end_time = request.GET.get('end_time', '')
    _form_data['end_time'] = end_time
    # 获取搜索框参数
    lab_number = request.GET.get('lab_number', '')
    try:
        # lab_number处理
        if not lab_number == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
        print(lab_number)
        print(111111111111111111)
        # 获取获取所有入库单号，组成列表
        receipt_doc_number_list = inventory_receipt.objects.values('doc_number').order_by('-doc_number').distinct()
        _form_data['receipt_doc_number_list'] = receipt_doc_number_list
        # 获取获取所有SKU，组成列表
        receipt_sku_list = inventory_receipt.objects.values('sku').order_by('-sku').distinct()
        _form_data['receipt_sku_list'] = receipt_sku_list
        # 获取获取所有仓库，组成列表
        receipt_wh_list = warehouse.objects.all()
        _form_data['receipt_wh_list'] = receipt_wh_list
        # 获取获取所有入库类型，组成列表
        receipt_doc_type_list = []
        invr_choices = inventory_receipt.DOC_TYPE_CHOICES
        for i in invr_choices:
            type_list = {'key': i[0], 'value': i[1]}
            receipt_doc_type_list.append(type_list)
        _form_data['receipt_doc_type_list'] = receipt_doc_type_list
        # 获取获取所有用户，组成列表
        receipt_user_list = inventory_receipt.objects.values('user_name').order_by('-user_name').distinct()
        _form_data['receipt_user_list'] = receipt_user_list
        # 获取入库记录
        query = {}  # 搜索参数
        if doc_number:
            query['doc_number'] = doc_number
        if sku:
            query['sku'] = sku
        if wh_code > 0:
            query['warehouse_id'] = wh_code
        if doc_type:
            query['doc_type'] = doc_type
        if user:
            query['user_name'] = user
        if start_time:
            query['created_at__gte'] = start_time
        if end_time:
            query['created_at__lt'] = end_time

        # lab_number不为空搜索
        if not lab_number == '':
            receipt_list = inventory_receipt.objects.filter(sku=lab_number).order_by("-doc_number", '-created_at')[0:10000]
        else:
            receipt_list = inventory_receipt.objects.filter(**query).order_by("-doc_number", '-created_at')[0:10000]
        _items = receipt_list
        _form_data['total'] = len(_items)  # 入库单总数

        # 入库单分页
        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page
        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_frame_receipt_report.html", {
            'form_data': _form_data,
            'list': _items,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_frame_receipt_report'),
            'filter': filter,
            'query_string': query_string,
            'paginator': paginator,  # 入库单分页对象
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_frame_receipt_report'),
        })


# 镜架入库记录报告导出excel
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_receipt_report_export_excel(request):
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '0')
    wh_code = int(wh_code)  # 镜架入库表存储的是仓库ID
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    # 获取入库记录
    query = {}  # 搜索参数
    if doc_number:
        query['doc_number'] = doc_number
    if sku:
        query['sku'] = sku
    if wh_code > 0:
        query['warehouse_id'] = wh_code
    if doc_type:
        query['doc_type'] = doc_type
    if user:
        query['user_name'] = user
    if start_time:
        query['created_at__gte'] = start_time
    if end_time:
        query['created_at__lt'] = end_time
    receipt_list = inventory_receipt.objects.filter(**query).order_by("-id")[0:10000]
    try:
        response = HttpResponse(content_type='text/csv')
        file_name = 'redirect_laborder_list'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '#', '入库编号', 'SKU', '仓库', '入库类型', '用户', '创建时间', '数量', '单号', '备注'
        ])

        for item in receipt_list:
            writer.writerow([
                item.id, item.doc_number, item.sku, item.warehouse.name, item.get_doc_type_display(),
                item.user_name, item.created_at, item.quantity, item.lab_number, item.comments,
            ])

        return response
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        return HttpResponse('导出遇到异常%s' % str(e))


# 镜架入库记录报告汇总打印
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_receipt_report_print(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    try:
        # 获取入库记录
        query = ''
        if doc_number:
            query += 'and doc_number=' + doc_number
        if sku:
            query += " and sku='" + sku + "'"
        if wh_code:
            query += " and warehouse_id=" + wh_code
        if doc_type:
            query += " and doc_type='" + doc_type + "'"
        if user:
            query += " and user_name='" + user + "'"
        if start_time:
            query += " and created_at>='" + start_time + "'"
        if end_time:
            query += " and created_at<'" + end_time + "'"
        query += ' GROUP BY sku ORDER BY sku,created_at'
        logging.debug('query=' + query)
        sql = '''select doc_number,sku,warehouse_id,doc_type,user_name,created_at,lab_number,comments,sum(quantity) as sum
                from wms_inventory_receipt where is_enabled=1 %s
            ''' % query
        # sql查询
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            from util.db_helper import *

            sql_query_list = namedtuplefetchall(cursor)
        # 重新封装调整显示效果
        wh_list = warehouse.objects.all()  # 仓库列表
        choice_list = inventory_receipt.DOC_TYPE_CHOICES
        for i in sql_query_list:
            item = {}
            item['doc_number'] = i.doc_number
            item['sku'] = i.sku
            for w in wh_list:
                if w.id == i.warehouse_id:
                    item['warehouse_id'] = w.name
            for c in choice_list:
                if c[0] == i.doc_type:
                    item['doc_type'] = c[1]
            item['user_name'] = i.user_name
            item['created_at'] = i.created_at
            item['lab_number'] = i.lab_number
            item['comments'] = i.comments
            item['sum'] = i.sum
            _items.append(item)
        return render(request, "inventory_frame_receipt_report_print.html", {
            'list': _items,
            'requestUrl': '/oms/inventory_frame_receipt_report/',
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_frame_delivery_report'),
        })


# 镜架出库记录报告
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_delivery_report(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应

    # 通过时间获取编号
    time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
    _form_data['time_now'] = time_now
    # 获取GET参数
    page = request.GET.get('page', 1)
    doc_number = request.GET.get('doc_number', '')
    _form_data['doc_number'] = doc_number
    sku = request.GET.get('sku', '')
    _form_data['sku'] = sku
    wh_code = request.GET.get('wh_code', '0')
    wh_code = int(wh_code)  # 镜架出库表存储的是仓库ID
    _form_data['wh_code'] = wh_code
    doc_type = request.GET.get('doc_type', '')
    _form_data['doc_type'] = doc_type
    user = request.GET.get('user', '')
    _form_data['user'] = user
    start_time = request.GET.get('start_time', '')
    _form_data['start_time'] = start_time
    end_time = request.GET.get('end_time', '')
    _form_data['end_time'] = end_time
    # 获取搜索框参数
    lab_number = request.GET.get('lab_number', '')
    try:
        # lab_number处理
        if not lab_number == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
        # 获取获取所有出库单号，组成列表
        delivery_doc_number_list = inventory_delivery.objects.values('doc_number').order_by('-doc_number').distinct()
        _form_data['delivery_doc_number_list'] = delivery_doc_number_list
        # 获取获取所有SKU，组成列表
        delivery_sku_list = inventory_delivery.objects.values('sku').order_by('-sku').distinct()
        _form_data['delivery_sku_list'] = delivery_sku_list
        # 获取获取所有仓库，组成列表
        delivery_wh_list = warehouse.objects.all()
        _form_data['delivery_wh_list'] = delivery_wh_list
        # 获取获取所有出库类型，组成列表
        delivery_doc_type_list = []
        invr_choices = inventory_delivery.DOC_TYPE_CHOICES
        for i in invr_choices:
            type_list = {'key': i[0], 'value': i[1]}
            delivery_doc_type_list.append(type_list)
        _form_data['delivery_doc_type_list'] = delivery_doc_type_list
        # 获取获取所有用户，组成列表
        delivery_user_list = inventory_delivery.objects.values('user_name').order_by('-user_name').distinct()
        _form_data['delivery_user_list'] = delivery_user_list
        # 获取出库记录
        query = {}  # 搜索参数
        if doc_number:
            query['doc_number'] = doc_number
        if sku:
            query['sku'] = sku
        if wh_code > 0:
            query['warehouse_id'] = wh_code
        if doc_type:
            query['doc_type'] = doc_type
        if user:
            query['user_name'] = user
        if start_time:
            query['created_at__gte'] = start_time
        if end_time:
            query['created_at__lt'] = end_time


        # lab_number不为空搜索
        if not lab_number == '':
            delivery_list = inventory_delivery.objects.filter(sku=lab_number).order_by("-doc_number", '-created_at')[0:10000]
        else:
            delivery_list = inventory_delivery.objects.filter(**query).order_by("-doc_number", '-created_at')[0:10000]
        _items = delivery_list

        _form_data['total'] = len(_items)  # 出库单总数

        # 出库单分页
        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page
        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_frame_delivery_report.html", {
            'form_data': _form_data,
            'list': _items,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_frame_delivery_report'),
            'filter': filter,
            'query_string': query_string,
            'paginator': paginator,  # 出库单分页对象
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_frame_delivery_report'),
        })


# 镜架出库记录报告导出excel
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_delivery_report_export_excel(request):
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '0')
    wh_code = int(wh_code)  # 镜架出库表存储的是仓库ID
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    # 获取出库记录
    query = {}  # 搜索参数
    if doc_number:
        query['doc_number'] = doc_number
    if sku:
        query['sku'] = sku
    if wh_code > 0:
        query['warehouse_id'] = wh_code
    if doc_type:
        query['doc_type'] = doc_type
    if user:
        query['user_name'] = user
    if start_time:
        query['created_at__gte'] = start_time
    if end_time:
        query['created_at__lt'] = end_time
    delivery_list = inventory_delivery.objects.filter(**query).order_by("-id")[0:10000]
    try:
        response = HttpResponse(content_type='text/csv')
        file_name = 'redirect_laborder_list'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '#', '出库编号', 'SKU', '仓库', '出库类型', '用户', '创建时间', '数量', '单号', '备注'
        ])

        for item in delivery_list:
            writer.writerow([
                item.id, item.doc_number, item.sku, item.warehouse.name, item.get_doc_type_display(),
                item.user_name, item.created_at, item.quantity, item.lab_number, item.comments,
            ])

        return response
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        return HttpResponse('导出遇到异常%s' % str(e))


# 镜架出库记录报告汇总打印
@login_required
@permission_required('wms.INVENTORY_FRAME_REPORT', login_url='/oms/forbid/')
def inventory_frame_delivery_report_print(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    try:
        # 获取出库记录
        query = ''
        if doc_number:
            query += 'and doc_number=' + doc_number
        if sku:
            query += " and sku='" + sku + "'"
        if wh_code:
            query += " and warehouse_id=" + wh_code
        if doc_type:
            query += " and doc_type='" + doc_type + "'"
        if user:
            query += " and user_name='" + user + "'"
        if start_time:
            query += " and created_at>='" + start_time + "'"
        if end_time:
            query += " and created_at<'" + end_time + "'"
        query += ' GROUP BY sku ORDER BY sku,created_at'
        logging.debug('sql=' + query)
        sql = '''select doc_number,sku,warehouse_id,doc_type,user_name,created_at,lab_number,comments,sum(quantity) as sum
                        from wms_inventory_delivery where is_enabled=1 %s
                    ''' % query
        # sql查询
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            from util.db_helper import *

            sql_query_list = namedtuplefetchall(cursor)
            # 重新封装调整显示效果
            wh_list = warehouse.objects.all()  # 仓库列表
            choice_list = inventory_delivery.DOC_TYPE_CHOICES
            for i in sql_query_list:
                item = {}
                item['doc_number'] = i.doc_number
                item['sku'] = i.sku
                for w in wh_list:
                    if w.id == i.warehouse_id:
                        item['warehouse_id'] = w.name
                for c in choice_list:
                    if c[0] == i.doc_type:
                        item['doc_type'] = c[1]
                    else:  # 库存结构中没有自动出库
                        item['doc_type'] = '系统自动'
                item['user_name'] = i.user_name
                item['created_at'] = i.created_at
                item['lab_number'] = i.lab_number
                item['comments'] = i.comments
                item['sum'] = i.sum
                _items.append(item)
        return render(request, "inventory_frame_delivery_report_print.html", {
            'list': _items,
            'requestUrl': '/oms/inventory_frame_receipt_report/',
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_frame_delivery_report'),
        })


# 镜片入库记录报告
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_receipt_report(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    page = request.GET.get('page', 1)
    doc_number = request.GET.get('doc_number', '')
    _form_data['doc_number'] = doc_number
    sku = request.GET.get('sku', '')
    _form_data['sku'] = sku
    wh_code = request.GET.get('wh_code', '')
    _form_data['wh_code'] = wh_code
    doc_type = request.GET.get('doc_type', '')
    _form_data['doc_type'] = doc_type
    user = request.GET.get('user', '')
    _form_data['user'] = user
    start_time = request.GET.get('start_time', '')
    _form_data['start_time'] = start_time
    end_time = request.GET.get('end_time', '')
    _form_data['end_time'] = end_time
    # 获取搜索框参数
    lab_number = request.GET.get('lab_number', '')
    try:
        # lab_number处理
        if not lab_number == "":
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

        # 获取获取所有入库单号，组成列表
        receipt_doc_number_list = inventory_receipt_lens.objects.values('doc_number').order_by('-doc_number').distinct()
        _form_data['receipt_doc_number_list'] = receipt_doc_number_list
        # 获取获取所有SKU，组成列表
        receipt_name_list = inventory_receipt_lens.objects.values('name', 'sku').order_by('name').distinct()
        _form_data['receipt_name_list'] = receipt_name_list
        # 获取获取所有仓库，组成列表
        receipt_wh_list = warehouse.objects.all()
        _form_data['receipt_wh_list'] = receipt_wh_list
        # 获取获取所有入库类型，组成列表
        receipt_doc_type_list = []
        invr_choices = inventory_receipt_lens.DOC_TYPE_CHOICES
        for i in invr_choices:
            type_list = {'key': i[0], 'value': i[1]}
            receipt_doc_type_list.append(type_list)
        _form_data['receipt_doc_type_list'] = receipt_doc_type_list
        # 获取获取所有用户，组成列表
        receipt_user_list = inventory_receipt_lens.objects.values('user_name').order_by('-user_name').distinct()
        _form_data['receipt_user_list'] = receipt_user_list
        # 获取入库记录
        query = {}  # 搜索参数
        if doc_number:
            query['doc_number'] = doc_number
        if sku:
            query['sku'] = sku
        if wh_code:
            query['warehouse_code'] = wh_code
        if doc_type:
            query['doc_type'] = doc_type
        if user:
            query['user_name'] = user
        if start_time:
            query['created_at__gte'] = start_time
        if end_time:
            query['created_at__lt'] = end_time
        receipt_list = inventory_receipt_lens.objects.filter(**query).order_by("-doc_number", '-created_at')[0:100000]
        # lab_number不为空搜索
        if not lab_number == "":
            receipt_list = inventory_receipt_lens.objects.filter(lab_number=lab_number)

        _items = receipt_list

        # _form_data['total'] = len(_items)  # 入库单总数

        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = _items.count()

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_lens_receipt_report.html", {
            'form_data': _form_data,
            'list': _items,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_lens_receipt_report'),
            'query_string': query_string,
            'paginator': paginator,
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Receipt'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_lens_receipt_report'),
        })


# 镜片入库记录报告导出excel
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_receipt_report_export_excel(request):
    # 获取GET参数

    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    # 获取入库记录
    query = {}  # 搜索参数
    if doc_number:
        query['doc_number'] = doc_number
    if sku:
        query['sku'] = sku
    if wh_code:
        query['warehouse_code'] = wh_code
    if doc_type:
        query['doc_type'] = doc_type
    if user:
        query['user_name'] = user
    if start_time:
        query['created_at__gte'] = start_time
    if end_time:
        query['created_at__lt'] = end_time
    receipt_list_lens = inventory_receipt_lens.objects.filter(**query).order_by("id")[0:100000]
    try:
        response = HttpResponse(content_type='text/csv')
        file_name = 'redirect_laborder_list'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '#', '入库编号', '镜片', '仓库', '入库类型', '用户', '创建时间', 'SPH', 'CYL', '数量', '单号', '备注'
        ])

        for item in receipt_list_lens:
            writer.writerow([
                item.id, item.doc_number, item.name, item.warehouse_name, item.get_doc_type_display(),
                item.user_name, item.created_at, item.sph, item.cyl, item.quantity, item.lab_number, item.comments,
            ])

        return response
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        return HttpResponse('导出遇到异常%s' % str(e))


# 镜片入库记录报告汇总打印
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_receipt_report_print(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    try:
        # 获取入库记录
        query = ''
        if doc_number:
            query += 'and doc_number=' + doc_number
        if sku:
            query += " and sku='" + sku + "'"
        if wh_code:
            query += " and warehouse_code='" + wh_code + "'"
        if doc_type:
            query += " and doc_type='" + doc_type + "'"
        if user:
            query += " and user_name='" + user + "'"
        if start_time:
            query += " and created_at>='" + start_time + "'"
        if end_time:
            query += " and created_at<'" + end_time + "'"
        query += ' GROUP BY sku,sph,cyl ORDER BY name,created_at'
        logging.debug('sql=' + query)
        sql = '''select doc_number,name,sph,cyl,warehouse_name,doc_type,user_name,created_at,lab_number,comments,sum(quantity) as sum
                        from wms_inventory_receipt_lens where is_enabled=1  %s
                    ''' % query
        # sql查询
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            from util.db_helper import *
            sql_query_list = namedtuplefetchall(cursor)
            # 重新封装调整显示效果
            choice_list = inventory_receipt_lens.DOC_TYPE_CHOICES
            for i in sql_query_list:
                item = {}
                item['doc_number'] = i.doc_number
                item['name'] = i.name
                item['sph'] = i.sph
                item['cyl'] = i.cyl
                item['warehouse_name'] = i.warehouse_name
                for c in choice_list:
                    if c[0] == i.doc_type:
                        item['doc_type'] = c[1]
                    elif i.doc_type == 'INIT':  # 库存结构中没有自动出库
                        item['doc_type'] = '系统自动'
                item['user_name'] = i.user_name
                item['created_at'] = i.created_at
                item['lab_number'] = i.lab_number
                item['comments'] = i.comments
                item['sum'] = i.sum
                _items.append(item)
        return render(request, "inventory_lens_receipt_report_print.html", {
            'list': _items,
            'requestUrl': '/oms/inventory_lens_delivery_report/',
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_lens_delivery_report'),
        })


# 镜片出库记录报告
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_delivery_report(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    page = request.GET.get('page', 1)
    doc_number = request.GET.get('doc_number', '')
    _form_data['doc_number'] = doc_number
    sku = request.GET.get('sku', '')
    _form_data['sku'] = sku
    wh_code = request.GET.get('wh_code', '')
    _form_data['wh_code'] = wh_code
    doc_type = request.GET.get('doc_type', '')
    _form_data['doc_type'] = doc_type
    user = request.GET.get('user', '')
    _form_data['user'] = user
    start_time = request.GET.get('start_time', '')
    _form_data['start_time'] = start_time
    end_time = request.GET.get('end_time', '')
    _form_data['end_time'] = end_time
    # 获取搜索框参数
    lab_number = request.GET.get('lab_number', '')
    try:
        # lab_number处理
        if not lab_number == "":
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

        # 获取获取所有出库单号，组成列表
        #delivery_doc_number_list = inventory_delivery_lens.objects.values('doc_number').order_by(
            #'-doc_number').distinct()
        _form_data['delivery_doc_number_list'] = []
        # 获取获取所有SKU，组成列表
        delivery_name_list = inventory_delivery_lens.objects.values('name', 'sku').order_by('name').distinct()
        _form_data['delivery_name_list'] = delivery_name_list
        # 获取获取所有仓库，组成列表
        delivery_wh_list = warehouse.objects.all()
        _form_data['delivery_wh_list'] = delivery_wh_list
        # 获取获取所有出库类型，组成列表
        delivery_doc_type_list = []
        invr_choices = inventory_delivery_lens.DOC_TYPE_CHOICES
        for i in invr_choices:
            type_list = {'key': i[0], 'value': i[1]}
            delivery_doc_type_list.append(type_list)
        _form_data['delivery_doc_type_list'] = delivery_doc_type_list
        # 获取获取所有用户，组成列表
        delivery_user_list = inventory_delivery_lens.objects.values('user_name').order_by('-user_name').distinct()
        _form_data['delivery_user_list'] = delivery_user_list
        # 获取出库记录
        query = {}  # 搜索参数
        if doc_number:
            query['doc_number'] = doc_number
        if sku:
            query['sku'] = sku
        if wh_code:
            query['warehouse_code'] = wh_code
        if doc_type:
            query['doc_type'] = doc_type
        if user:
            query['user_name'] = user
        if start_time:
            query['created_at__gte'] = start_time
        if end_time:
            query['created_at__lt'] = end_time
        delivery_list = inventory_delivery_lens.objects.filter(**query).order_by('-created_at')[0:100000]
        # lab_number不为空搜索
        if not lab_number == "":
            delivery_list = inventory_delivery_lens.objects.filter(lab_number=lab_number)

        _items = delivery_list


        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = _items.count()

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_lens_delivery_report.html", {
            'form_data': _form_data,
            'list': _items,
            'response_message': rm,
            'requestUrl': reverse('wms_inventory_lens_delivery_report'),
            'query_string': query_string,
            'paginator': paginator,
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_lens_delivery_report'),
        })


# 镜片出库记录报告导出excel
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_delivery_report_export_excel(request):
    # 获取GET参数

    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    # 获取出库记录
    query = {}  # 搜索参数
    if doc_number:
        query['doc_number'] = doc_number
    if sku:
        query['sku'] = sku
    if wh_code:
        query['warehouse_code'] = wh_code
    if doc_type:
        query['doc_type'] = doc_type
    if user:
        query['user_name'] = user
    if start_time:
        query['created_at__gte'] = start_time
    if end_time:
        query['created_at__lt'] = end_time
    delivery_list_lens = inventory_delivery_lens.objects.filter(**query).order_by("id")[0:100000]
    try:
        response = HttpResponse(content_type='text/csv')
        file_name = 'redirect_laborder_list'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '#', '出库编号', '镜片', '仓库', '出库类型', '用户', '创建时间', 'SPH', 'CYL', '数量', '单号', '备注'
        ])

        for item in delivery_list_lens:
            writer.writerow([
                item.id, item.doc_number, item.name, item.warehouse_name, item.get_doc_type_display(),
                item.user_name, item.created_at, item.sph, item.cyl, item.quantity, item.lab_number, item.comments,
            ])

        return response
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        return HttpResponse('导出遇到异常%s' % str(e))


# 镜片出库记录报告汇总打印
@login_required
@permission_required('wms.INVENTORY_LENS_REPORT', login_url='/oms/forbid/')
def inventory_lens_delivery_report_print(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    doc_number = request.GET.get('doc_number', '')
    sku = request.GET.get('sku', '')
    wh_code = request.GET.get('wh_code', '')
    doc_type = request.GET.get('doc_type', '')
    user = request.GET.get('user', '')
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    try:
        # 获取出库记录
        query = ''
        if doc_number:
            query += 'and doc_number=' + doc_number
        if sku:
            query += " and sku='" + sku + "'"
        if wh_code:
            query += " and warehouse_code='" + wh_code + "'"
        if doc_type:
            query += " and doc_type='" + doc_type + "'"
        if user:
            query += " and user_name='" + user + "'"
        if start_time:
            query += " and created_at>='" + start_time + "'"
        if end_time:
            query += " and created_at<'" + end_time + "'"
        query += ' GROUP BY sku,sph,cyl ORDER BY name,created_at'
        logging.debug('sql=' + query)
        sql = '''select doc_number,name,sph,cyl,warehouse_name,doc_type,user_name,created_at,lab_number,comments,sum(quantity) as sum
                from wms_inventory_delivery_lens where is_enabled=1  %s
            ''' % query

        # sql查询
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            from util.db_helper import *

            sql_query_list = namedtuplefetchall(cursor)
            # 重新封装调整显示效果
            choice_list = inventory_delivery_lens.DOC_TYPE_CHOICES
            for i in sql_query_list:
                item = {}
                item['doc_number'] = i.doc_number
                item['name'] = i.name
                item['sph'] = i.sph
                item['cyl'] = i.cyl
                item['warehouse_name'] = i.warehouse_name
                for c in choice_list:
                    if c[0] == i.doc_type:
                        item['doc_type'] = c[1]
                    elif i.doc_type == 'AUTO':  # 库存结构中没有自动出库
                        item['doc_type'] = '系统自动'
                item['user_name'] = i.user_name
                item['created_at'] = i.created_at
                item['lab_number'] = i.lab_number
                item['comments'] = i.comments
                item['sum'] = i.sum
                _items.append(item)
        return render(request, "inventory_lens_delivery_report_print.html", {
            'list': _items,
            'requestUrl': '/oms/inventory_lens_delivery_report/',
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_inventory_lens_delivery_report'),
        })


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_product_management(request):
    '''
    库存列表 V2
    :param request:
    :return:
    '''
    _form_data = {}
    _items = []
    try:
        page = request.GET.get('page', 1)
        sku = request.GET.get('sku', '')
        sort_filter = request.GET.get('sort_filter', 'all')
        _filter = request.GET.get('filter', 'all')
        status_filter = request.GET.get('status_filter', 'all')
        currentPage = int(page)
        with connections['pg_oms_query'].cursor() as cursor:
            sql = '''SELECT
                            t0.id,
                            t0.sku,
                            t1.name,
                            t0.quantity,
                            t0.lock_quantity,
                            t0.reserve_quantity,
                            t0.no_sale_quantity,
                            t0.ch_quantity,
                            t0.al_quantity,
                            t0.retired,
                            t0.estimate_replenishment_date,
                            t0.web_status,
                            t0.web_quantity,
                            t0.oms_web_diff,
                            t0.last_out_of_stock,
                            t0.last_in_stock,
                            t0.last_retired,
                            t0.last_sign,
                            t0.status
                        FROM
                            wms_inventory_struct AS t0
                        LEFT JOIN wms_product_frame AS t1 ON t0.sku = t1.sku '''
            if sku != '':
                sql = sql + ''' WHERE t0.sku LIKE "%%%s%%" ''' % sku
            elif  _filter == 'all':
                sql = sql + ''' WHERE t0.retired <> True '''
            else:
                if _filter.lower() == 'retired':
                    sql = sql + ''' WHERE t0.retired = True '''
                else:
                    sql = sql + ''' WHERE t0.status="%s" AND t0.retired <> True ''' % _filter.upper()


            if sort_filter == '1':
                sql = sql + ''' ORDER BY oms_web_diff '''
                # iiss = iiss.order_by('oms_web_diff')
            elif sort_filter == '2':
                sql = sql + ''' AND quantity <= 50 ORDER BY quantity '''
                # iiss = iiss.filter(quantity__lte=50).order_by('quantity')
            elif sort_filter == '3':
                sql = sql + ''' AND oms_web_diff=0 ORDER BY quantity '''
                # iiss = iiss.filter(oms_web_diff=0).order_by('quantity')
            elif sort_filter == '4':
                sql = sql + ''' AND oms_web_diff<>0 ORDER BY quantity '''
                # iiss = iiss.exclude(oms_web_diff=0).order_by('quantity')
            elif sort_filter == '5':
                sql = sql + '''  ORDER BY al_quantity DESC '''
                # iiss = iiss.order_by('-al_quantity')
            else:
                sql = sql + '''  ORDER BY quantity '''
                # iiss = iiss.order_by('quantity')

            cursor.execute(sql)
            iiss = namedtuplefetchall(cursor)


        for iis in iiss:
            if status_filter == 'status_diff':
                if iis.status != iis.web_status:
                    _items.append({
                        'id': iis.id,
                        'sku': iis.sku,
                        'name': iis.name,
                        'status': iis.status,
                        'quantity': iis.quantity,
                        'lock_quantity': iis.lock_quantity,
                        'reserve_quantity': iis.reserve_quantity,
                        'no_sale_quantity': iis.no_sale_quantity,
                        'ch_quantity': iis.ch_quantity,
                        'al_quantity': iis.al_quantity,
                        'retired': iis.retired,
                        'web_status': iis.web_status,
                        'web_quantity': iis.web_quantity,
                        'oms_web_diff': iis.oms_web_diff,
                        'last_out_of_stock': iis.last_out_of_stock,
                        'last_in_stock': iis.last_in_stock,
                        'last_retired': iis.last_retired,
                        'last_sign': iis.last_sign,
                        'estimate_replenishment_date':iis.estimate_replenishment_date
                    })
            elif status_filter == 'status_same':
                if iis.status == iis.web_status:
                    _items.append({
                        'id': iis.id,
                        'sku': iis.sku,
                        'name': iis.name,
                        'status': iis.status,
                        'quantity': iis.quantity,
                        'lock_quantity': iis.lock_quantity,
                        'reserve_quantity': iis.reserve_quantity,
                        'no_sale_quantity': iis.no_sale_quantity,
                        'ch_quantity': iis.ch_quantity,
                        'al_quantity': iis.al_quantity,
                        'retired': iis.retired,
                        'web_status': iis.web_status,
                        'web_quantity': iis.web_quantity,
                        'oms_web_diff': iis.oms_web_diff,
                        'last_out_of_stock': iis.last_out_of_stock,
                        'last_in_stock': iis.last_in_stock,
                        'last_retired': iis.last_retired,
                        'last_sign': iis.last_sign,
                        'estimate_replenishment_date': iis.estimate_replenishment_date
                    })
            else:
                _items.append({
                    'id': iis.id,
                    'sku': iis.sku,
                    'name': iis.name,
                    'status': iis.status,
                    'quantity': iis.quantity,
                    'lock_quantity': iis.lock_quantity,
                    'reserve_quantity': iis.reserve_quantity,
                    'no_sale_quantity': iis.no_sale_quantity,
                    'ch_quantity': iis.ch_quantity,
                    'al_quantity': iis.al_quantity,
                    'retired': iis.retired,
                    'web_status': iis.web_status,
                    'web_quantity': iis.web_quantity,
                    'oms_web_diff': iis.oms_web_diff,
                    'last_out_of_stock': iis.last_out_of_stock,
                    'last_in_stock': iis.last_in_stock,
                    'last_retired': iis.last_retired,
                    'last_sign': iis.last_sign,
                    'estimate_replenishment_date': iis.estimate_replenishment_date
                })
        # 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = len(_items)
        paginator = Paginator(_items, oms.const.PAGE_SIZE_MORE)
        try:
            page_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_items = paginator.page(paginator.num_pages)

        return render(request, "product_management.html", {
            'currentPage': currentPage,
            'paginator': paginator,
            'list': page_items,
            'form_data': _form_data,
            'filter': _filter,
            'sort_filter': sort_filter,
            'status_filter': status_filter,
            'requestUrl': reverse('wms_product_management'),
            'query_string': query_string,
            'all_list': _items
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
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def inventory_dis_quantity(request):
    """分配數量"""
    rm = util.response.response_message.response_dict()
    try:
        sku = request.POST.get('sku', '')
        quantity = request.POST.get('quantity', 0)
        flag = request.POST.get('flag', '')
        p_number = datetime.datetime.now().strftime('%Y%m%d')
        channel_code = request.POST.get('channel_code', '')
        if flag == 'distribution':
            ircs = inventory_receipt_channel.objects.filter(success_status='1', sku=sku)
            if len(ircs) > 0 and sku != '':
                rm['code'] = -1
                rm['message'] = '入库申请单中有未执行成功的未处理，请到分配&撤回操作清单处理'
                return JsonResponse(rm)
            ircc = inventory_receipt_channel_controller()
            res = ircc.add(request, p_number, channel_code, 'ALLOCATION', sku, int(quantity))
            ois = inventory_struct.objects.get(sku=sku)
            al_quantity = int(ois.al_quantity) - int(quantity)
            if al_quantity <= 0:
                al_quantity = 0

            ois.al_quantity = al_quantity
            ois.save()
        else:
            idcs = inventory_delivery_channel.objects.filter(success_status='1', sku=sku, doc_type='RECALL')
            if len(idcs) > 0 and sku != '':
                rm['code'] = -1
                rm['message'] = '出库申请单中有未执行成功的未处理，请到分配&撤回操作清单处理'
                return JsonResponse(rm)

            idcc = inventory_delivery_channel_controller()
            res = idcc.add(request, p_number, channel_code, 'RECALL', sku, int(quantity))
            ois = inventory_struct.objects.get(sku=sku)
            ois.al_quantity = int(ois.al_quantity) + int(quantity)
            ois.save()

        if not res.code == 0:
            rm['code'] = -1
            rm['message'] = res.message
            return JsonResponse(rm)

        rm['code'] = 0
        rm['message'] = '执行成功'
        return JsonResponse(rm)
    except Exception as e:
        print(e)
        rm["code"] = -1
        rm['message'] = str(e)
        rm["error"] = "执行失败 请重试:" + str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.DISTRIBUTION_WITHDRAWAL_LIST', login_url='/oms/forbid/')
def redirect_distribution_withdrawal_list(request):
    '''
    分配&撤回列表
    :param request:
    :return:
    '''
    _form_data = {}
    _items = []
    try:
        page = request.GET.get('page', 1)
        sku = request.GET.get('sku', '')
        _filter = request.GET.get('filter', 'all')
        ircs = []
        idcs = []
        currentPage = int(page)
        if sku != '':
            idcs = inventory_delivery_channel.objects.filter(sku=sku, doc_type='RECALL').values()
            ircs = inventory_receipt_channel.objects.filter(sku=sku).values()
        elif _filter == 'all':
            idcs = inventory_delivery_channel.objects.filter(doc_type='RECALL').values()
            ircs = inventory_receipt_channel.objects.filter().values()
        else:
            if _filter == 'OIRC':
                ircs = inventory_receipt_channel.objects.filter().values()
            else:
                idcs = inventory_delivery_channel.objects.filter(doc_type='RECALL').values()
        ircs_dict_list = list(ircs)
        idcs_dict_list = list(idcs)
        _items.extend(ircs_dict_list)
        _items.extend(idcs_dict_list)

        from operator import itemgetter
        _items.sort(key=itemgetter('created_at'), reverse=True)

        # 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = len(_items)
        paginator = Paginator(_items, oms.const.PAGE_SIZE)
        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "distribution_withdrawal_list.html", {
            'currentPage': currentPage,
            'paginator': paginator,
            'list': _items,
            'form_data': _form_data,
            'filter': _filter,
            'requestUrl': reverse('wms_distribution_withdrawal_list'),
            'query_string': query_string,
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
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_inventory_again_dis_quantity(request):
    """重新分配數量"""
    rm = util.response.response_message.response_dict()
    try:
        sku = request.POST.get('sku', '')
        quantity = request.POST.get('quantity', 0)
        flag = request.POST.get('flag', '')
        channel_code = request.POST.get('channel_code', '')
        p_number = datetime.datetime.now().strftime('%Y%m%d')

        wi = web_inventory()
        stock_data = [{"sku": sku,
                       "web_sku": '',
                       "quantity": int(quantity),
                       "doc_type": '',
                       "relevant_number": p_number,
                       "options": ""}]

        if flag == 'distribution':
            stock_data[0]['doc_type'] = 'GENERAL_IN'
            oirc = inventory_receipt_channel.objects.get(sku=sku, channel_code=channel_code, success_status='1')
            data = wi.web_invs_receipt(stock_data)
            if data["code"] == 0:
                oirc.success_status = '0'
                oirc.message = data["message"].encode('raw_unicode_escape')
                oirc.save()
                rm['code'] = 0
                rm['message'] = '執行成功'
            else:
                oirc.success_status = '1'
                oirc.message = data["message"]
                oirc.save()
                rm['code'] = -1
                rm['message'] = "exception:" + data["message"]
        else:
            stock_data[0]['doc_type'] = 'GENERAL_OUT'
            oidc = inventory_delivery_channel.objects.get(sku=sku, channel_code=channel_code, success_status='1')
            data = wi.web_invs_delivery(stock_data)
            if data["code"] == 0:
                oidc.success_status = '0'
                oidc.message = data["message"]
                oidc.save()
                rm['code'] = 0
                rm['message'] = '执行成功'
            else:
                oidc.success_status = '1'
                oidc.message = data["message"].encode('raw_unicode_escape')
                oidc.save()
                rm['code'] = -1
                rm['message'] = "exception:" + data["message"]

        return JsonResponse(rm)
    except Exception as e:
        rm["code"] = -1
        rm['message'] = str(e)
        rm["error"] = "执行失败 请重试:" + str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_inventory_sync_web_data(request):
    rm = util.response.response_message.response_dict()
    try:

        if request.method=="POST":
            iis = None
            sku = request.POST.get("sku", "")
            data = inventory_struct_contoller().sync_web_data(sku)
            # if type(data).__name__ == 'list':
            #     for item in data:
            #         iiss = inventory_struct.objects.filter(sku=item['sku'])
            #         if len(iiss) > 0:
            #             iis = iiss[0]
            #             qty = iis.quantity - iis.reserve_quantity - int(item['quantity_on_stock']) - iis.lock_quantity
            #             iis.web_quantity = item['quantity_on_stock']
            #             iis.web_status = item['status']
            #             iis.oms_web_diff = qty
            #             iis.save()
            # else:
            #     if data['code'] == 0:
            #         item = data['objects'][sku]['options']
            #         iis = inventory_struct.objects.get(sku=sku)
            #         qty = iis.quantity - iis.reserve_quantity - int(item['quantity_on_stock']) - iis.lock_quantity
            #         iis.web_quantity = item['quantity_on_stock']
            #         iis.web_status = item['status']
            #         iis.oms_web_diff = qty
            #         iis.save()

            if data['code'] == '0':
                rm["code"] = 0
                rm['message'] = ''
                return JsonResponse(rm)

            rm["code"] = -1
            rm['message'] = '執行失败'
            return JsonResponse(rm)
        rm["code"] = -1
        rm['message'] = 'GET方法不支持'
        return JsonResponse(rm)
    except Exception as e:
        rm["code"] = -1
        rm['message'] = str(e)
        rm["error"] = "執行失败 请重试:" + str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_inventory_sync_reserve_quantity(request):
    rm = util.response.response_message.response_dict()
    try:
        iis = None
        sku = request.GET.get("sku", "")

        if sku != '':
            sql = """SELECT i.frame AS frame, 
                            i.quantity AS quantity 
                     FROM oms_pgorderitem AS i 
                       LEFT JOIN oms_pgorder AS p 
                       ON  i.pg_order_entity_id = p.id 
                     WHERE p.is_inlab=FALSE 
                       AND p.status <> 'closed'
                       AND p.status <> 'canceled'
                       AND i.frame LIKE '%%%s%%'
            """ % sku
            with connections['pg_oms_query'].cursor() as cursor:
                iis = inventory_struct.objects.get(sku=sku)
                iis.reserve_quantity = 1
                iis.save()
                cursor.execute(sql)
                items = namedtuplefetchall(cursor)
                qty = 0
                for item in items:
                    qty = qty + int(item.quantity)
                lab_sql = """SELECT frame, quantity FROM oms_laborder  WHERE frame="%s" AND (`status` in ('', NULL, 'REQUEST_NOTES') OR (`status`='ONHOLD' AND current_status in ('', NULL, 'REQUEST_NOTES')))""" % sku

                cursor.execute(lab_sql)
                laborders = namedtuplefetchall(cursor)
                for item in laborders:
                    qty = qty + int(item.quantity)
                iis.reserve_quantity = qty
                iis.save()
        else:
            inventory_struct.objects.all().update(reserve_quantity=0)
            sql = """SELECT i.frame as frame, 
                          SUM(i.quantity) AS quantity 
                   FROM oms_pgorder AS p 
                     LEFT JOIN oms_pgorderitem AS i 
                     ON p.id = i.pg_order_entity_id 
                   WHERE p.is_inlab=FALSE                     
                        AND p.status <> 'closed'
                        AND p.status <> 'canceled' GROUP BY i.frame
            """
            poc = pgorder_frame_controller()
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                items = namedtuplefetchall(cursor)
                for item in items:
                    try:
                        res_rm = poc.get_lab_frame({"pg_frame": item.frame})
                        #frame = item.frame[1:8]
                        frame = res_rm.obj['lab_frame']
                        iis = inventory_struct.objects.get(sku=frame)
                        qty = iis.reserve_quantity + item.quantity
                        iis.reserve_quantity = qty
                        iis.save()
                    except Exception as e:
                        pass

                lab_sql = """SELECT frame, SUM(quantity) AS quantity FROM oms_laborder  WHERE (`status` in ('', NULL, 'REQUEST_NOTES') OR (`status`='ONHOLD' AND current_status in ('', NULL, 'REQUEST_NOTES'))) GROUP BY frame"""
                cursor.execute(lab_sql)
                laborders = namedtuplefetchall(cursor)
                for item in laborders:
                    try:
                        iis = inventory_struct.objects.get(sku=item.frame)
                        qty = iis.reserve_quantity + item.quantity
                        iis.reserve_quantity = qty
                        iis.save()
                    except Exception as e:
                        pass

        rm["code"] = 0
        rm['message'] = ''
        return JsonResponse(rm)
    except Exception as e:
        rm["code"] = -1
        rm['message'] = str(e)
        rm["error"] = "執行失败 请重试:" + str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_inventory_sync_difference(request):
    rm = util.response.response_message.response_dict()
    try:
        res = None
        sku = request.GET.get('sku', '')
        diff_quantity = request.GET.get('diff_quantity', 0)
        p_number = datetime.datetime.now().strftime('%Y%m%d')
        isc = inventory_struct_contoller()
        reserve_data = isc.sync_reserve_quantity(sku)
        if reserve_data['code'] == '0':
            web_data = isc.sync_web_data(sku)
            if web_data['code'] == '0':
                if int(diff_quantity) > 0:
                    wi = web_inventory()
                    stock_data = [{"sku": sku,
                                   "web_sku": '',
                                   "quantity": int(diff_quantity),
                                   "doc_type": 'ALLOCATION',
                                   "relevant_number": p_number,
                                   "options": ""}]
                    res = wi.web_invs_receipt(stock_data)

                elif int(diff_quantity) < 0:
                    wi = web_inventory()
                    stock_data = [{"sku": sku,
                                   "web_sku": '',
                                   "quantity": int(abs(int(diff_quantity))),
                                   "doc_type": 'RECALL',
                                   "relevant_number": p_number,
                                   "options": ""}]
                    res = wi.web_invs_delivery(stock_data)
            else:
                rm["code"] = -1
                rm['message'] = "同步该sku网站数据错误"
                rm["error"] = "同步该sku网站数据错误"
                return JsonResponse(rm)
        else:
            rm["code"] = -1
            rm['message'] = "重新计算该sku预定数量错误"
            rm["error"] = "重新计算该sku预定数量错误"
            return JsonResponse(rm)

        if not res["code"] == 0:
            rm['code'] = -1
            rm['message'] = res['message']
            return JsonResponse(rm)

        new_data = isc.sync_web_data(sku)
        if new_data['code'] == '0':
            rm['code'] = 0
            rm['message'] = '执行成功'
            return JsonResponse(rm)
        else:
            rm['code'] = -1
            rm['message'] = '请手动点击同步该sku网站数据按钮'
            return JsonResponse(rm)

    except Exception as e:
        rm["code"] = -1
        rm['message'] = str(e)
        rm["error"] = "执行失败 请重试:" + str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_inventory_sync_reason(request):
    rm = util.response.response_message.response_dict()
    sku = request.GET.get("sku")
    try:
        ot = inventory_operation_log_controller()
        reason_list = ot.inventory_operation_logs(sku)
        reason_list = json.dumps(reason_list, cls=DateEncoder)
        return HttpResponse(reason_list)
    except Exception as e:
        rm["code"] = -1
        rm['message'] = str(e)
        return JsonResponse(rm)


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_product_management_new(request):
    '''
    库存列表 V2
    :param request:
    :return:
    '''
    # _form_data = {}
    # _items = []
    # try:
    #     page = request.GET.get('page', 1)
    #     sku = request.GET.get('sku', '')
    #     sort_filter = request.GET.get('sort_filter', 'all')
    #     _filter = request.GET.get('filter', 'all')
    #     status_filter = request.GET.get('status_filter', 'all')
    #     currentPage = int(page)
    #     sql="select t0.sku,t0.status,t0.quantity,t0.lock_quantity,t0.reserve_quantity,t0.ch_quantity,t0.al_quantity,t0.retired," \
    #         "t0.web_status,t0.web_quantity,t0.oms_web_diff from wms_inventory_struct t0 left join wms_inventory_operation_log t1 on t0.sku=" \
    #         "(select t3.sku from wms_inventory_operation_log t3 where t3.sku=t0.sku order by t3.created_at desc limit 1);"
    #     if sku != '':
    #         sql +=""" and t0.sku=%s """ sku
    #     if sku != '':
    #         iiss = inventory_struct.objects.filter(sku=sku)
    #         if len(iiss) == 0:
    #             iiss = inventory_struct.objects.filter(sku__contains=sku)
    #     elif _filter == 'all':
    #         iiss = inventory_struct.objects.all().exclude(retired=True)
    #     else:
    #         if _filter.lower() == 'retired':
    #             iiss = inventory_struct.objects.filter(retired=True)
    #         else:
    #             iiss = inventory_struct.objects.filter(status=_filter.upper()).exclude(retired=True)
    #
    #     if sort_filter == '1':
    #         iiss = iiss.order_by('oms_web_diff')
    #     elif sort_filter == '2':
    #         iiss = iiss.filter(quantity__lte=50).order_by('quantity')
    #     elif sort_filter == '3':
    #         iiss = iiss.filter(oms_web_diff=0).order_by('quantity')
    #     elif sort_filter == '4':
    #         iiss = iiss.exclude(oms_web_diff=0).order_by('quantity')
    #     else:
    #         iiss = iiss.order_by('quantity')
    #
    #     for iis in iiss:
    #         #获取最新下架原因
    #         # ot = inventory_operation_log_controller()
    #         # rm = ot.inventory_operation_logs(iis.sku)
    #         reason = ''
    #         # if len(rm)>0:
    #         #   # 取出最新得下架原因
    #         #    reason=rm[0].reason
    #         if status_filter == 'status_diff':
    #             if iis.status != iis.web_status:
    #                 _items.append({
    #                     'sku': iis.sku,
    #                     'status': iis.status,
    #                     'quantity': iis.quantity,
    #                     'lock_quantity': iis.lock_quantity,
    #                     'reserve_quantity': iis.reserve_quantity,
    #                     'ch_quantity': iis.ch_quantity,
    #                     'al_quantity': iis.al_quantity,
    #                     'retired': iis.retired,
    #                     'web_status': iis.web_status,
    #                     'web_quantity': iis.web_quantity,
    #                     'oms_web_diff': iis.oms_web_diff,
    #                     'reason':reason
    #                 })
    #         elif status_filter == 'status_same':
    #             if iis.status == iis.web_status:
    #                 _items.append({
    #                     'sku': iis.sku,
    #                     'status': iis.status,
    #                     'quantity': iis.quantity,
    #                     'lock_quantity': iis.lock_quantity,
    #                     'reserve_quantity': iis.reserve_quantity,
    #                     'ch_quantity': iis.ch_quantity,
    #                     'al_quantity': iis.al_quantity,
    #                     'retired': iis.retired,
    #                     'web_status': iis.web_status,
    #                     'web_quantity': iis.web_quantity,
    #                     'oms_web_diff': iis.oms_web_diff,
    #                     'reason': reason
    #                 })
    #         else:
    #             _items.append({
    #                 'sku': iis.sku,
    #                 'status': iis.status,
    #                 'quantity': iis.quantity,
    #                 'lock_quantity': iis.lock_quantity,
    #                 'reserve_quantity': iis.reserve_quantity,
    #                 'ch_quantity': iis.ch_quantity,
    #                 'al_quantity': iis.al_quantity,
    #                 'retired': iis.retired,
    #                 'web_status': iis.web_status,
    #                 'web_quantity': iis.web_quantity,
    #                 'oms_web_diff': iis.oms_web_diff,
    #                 'reason': reason
    #             })
    #     # 获取URL中除page外的其它参数
    #     query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    #     if query_string:
    #         query_string = '&' + query_string
    #
    #     _form_data['total'] = len(_items)
    #     paginator = Paginator(_items, oms.const.PAGE_SIZE_MORE)
    #     try:
    #         page_items = paginator.page(page)
    #     except PageNotAnInteger:
    #         # If page is not an integer, deliver first page.
    #         page_items = paginator.page(1)
    #     except EmptyPage:
    #         # If page is out of range (e.g. 9999), deliver last page of results.
    #         page_items = paginator.page(paginator.num_pages)
    #
    #     return render(request, "product_management.html", {
    #         'currentPage': currentPage,
    #         'paginator': paginator,
    #         'list': page_items,
    #         'form_data': _form_data,
    #         'filter': _filter,
    #         'sort_filter': sort_filter,
    #         'status_filter': status_filter,
    #         'requestUrl': reverse('wms_product_management'),
    #         'query_string': query_string,
    #         'all_list': _items
    #     })
    # except Exception as e:
    #     logging.debug('Exception: %s' % e.message)
    #     _form_data['exceptions'] = e
    #     _form_data['error_message'] = e.message
    #     return render(request, "exceptions.html",
    #                   {
    #                       'form_data': _form_data,
    #                   })


# 仓位管理
@login_required
@permission_required('wms.LOCKERS_LIST', login_url='/oms/forbid/')
def lockers_list(request):
    _form_data = {}
    items = {}
    new_lists = []
    lb_list = []
    form = {}
    list = []
    storage_location_locker_num = ''
    order_number = request.GET.get('order_number', '')
    glass_max = int(request.GET.get('glass_max', '0'))
    is_vender = request.GET.get('is_vender', '0')
    location = request.GET.get('location', '')
    config_list = ''
    status = ''
    lab_number = ''
    try:
        with connections['default'].cursor() as cursor:
            sql = """SELECT * from wms_lockers_config"""
            cursor.execute(sql)
            config_list = namedtuplefetchall(cursor)
            if order_number <> '':
                objs = []
                loc = lab_order_controller()
                objs = loc.get_by_entity(order_number)
                if len(objs) > 0:
                    lab_number = objs[0].lab_number
                elif len(objs) == 0:
                    lab_number = order_number
                sql_list = """select t0.lab_number,t1.storage_location,t1.locker_num,t0.act_lens_name,t0.vendor,t0.status from oms_laborder t0,wms_lockers_item t1
where t0.lab_number=t1.lab_number and t0.lab_number like '%%%s%%'""" % lab_number
                cursor.execute(sql_list)
                lb_list = namedtuplefetchall(cursor)
            else:
                sql_list = """select * from wms_lockers where storage_location='%s'""" % (
                    location)
                lockercon = locker_controller()
                if glass_max > 0:
                    cursor.execute(sql_list)
                    all_list = namedtuplefetchall(cursor)
                    new_lists == all_list
                    for item in all_list:
                        if item.quantity > 0 and item.quantity < glass_max:
                            items['class'] = 'green'
                            items['storage_location'] = item.storage_location
                            items['locker_num'] = item.locker_num
                            items['quantity'] = item.quantity
                            items['vender'] = item.vender
                            items['id'] = item.id
                            # 查询item
                            item_green_sql = """select * from wms_lockers_item where locker_num=%s and storage_location='%s'""" % (
                                item.locker_num, item.storage_location)
                            cursor.execute(item_green_sql)
                            green_list = namedtuplefetchall(cursor)
                            for laborder in green_list:
                                obj = LabOrder.objects.get(lab_number=laborder.lab_number)
                                status = lockercon.get_status_cn(obj.status)
                                form['status'] = status
                                form['lab_number'] = laborder.lab_number
                                form['order_number'] = laborder.order_number
                                form['vendor'] = laborder.vendor
                                form['storage_location'] = laborder.storage_location
                                form['locker_num'] = laborder.locker_num
                                form['create_at'] = laborder.create_at
                                form['username'] = laborder.username
                                list.append(form)
                                form = {}
                            items['item'] = list
                            new_lists.append(items)
                            items = {}
                            list = []
                        if item.quantity == glass_max:
                            items['class'] = 'red'
                            items['storage_location'] = item.storage_location
                            items['locker_num'] = item.locker_num
                            items['quantity'] = item.quantity
                            items['vender'] = item.vender
                            items['id'] = item.id
                            # 查询item
                            item_red_sql = """select * from wms_lockers_item where locker_num=%s and storage_location='%s'""" % (
                                item.locker_num, item.storage_location)
                            cursor.execute(item_red_sql)
                            red_list = namedtuplefetchall(cursor)
                            for laborder in red_list:
                                obj = LabOrder.objects.get(lab_number=laborder.lab_number)
                                status = lockercon.get_status_cn(obj.status)
                                form['status'] = status
                                form['lab_number'] = laborder.lab_number
                                form['order_number'] = laborder.order_number
                                form['vendor'] = laborder.vendor
                                form['storage_location'] = laborder.storage_location
                                form['locker_num'] = laborder.locker_num
                                form['create_at'] = laborder.create_at
                                form['username'] = laborder.username
                                list.append(form)
                                form = {}
                            items['item'] = list
                            new_lists.append(items)
                            items = {}
                            list = []
                        if item.quantity == 0:
                            items['class'] = 'gray'
                            items['storage_location'] = item.storage_location
                            items['locker_num'] = item.locker_num
                            items['quantity'] = item.quantity
                            items['vender'] = item.vender
                            items['id'] = item.id
                            # 查询item
                            item_red_sql = """select * from wms_lockers_item where locker_num=%s and storage_location='%s'""" % (
                                item.locker_num, item.storage_location)
                            cursor.execute(item_red_sql)
                            gary_list = namedtuplefetchall(cursor)
                            for laborder in gary_list:
                                obj = LabOrder.objects.get(lab_number=laborder.lab_number)
                                status = lockercon.get_status_cn(obj.status)
                                form['status'] = status
                                form['lab_number'] = laborder.lab_number
                                form['order_number'] = laborder.order_number
                                form['vendor'] = laborder.vendor
                                form['storage_location'] = laborder.storage_location
                                form['locker_num'] = laborder.locker_num
                                form['create_at'] = laborder.create_at
                                form['username'] = laborder.username
                                list.append(form)
                                form = {}
                            items['item'] = list
                            new_lists.append(items)
                            items = {}
                            list = []

        if len(lb_list) > 0:
            storage_location_locker_num = lb_list[0].storage_location + "-" + lb_list[0].locker_num

        return render(request, "laborder_lockers_list.html",
                      {
                          'form_data': _form_data,
                          'new_lists': new_lists,
                          'config_list': config_list,
                          'location': location,
                          'glass_max': glass_max,
                          'lb_list': lb_list,
                          'lb_list_count': len(lb_list),
                          'storage_location_locker_num': storage_location_locker_num,
                          'order_number': order_number,
                          'is_vender': is_vender,
                          'requestUrl': '/wms/wms_lockers_list/'
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data
                      })


# 初始化仓位
@login_required
@permission_required('wms.LOCKERS_INIT', login_url='/oms/forbid/')
def init_lockers(request):
    glasses_max_limit = int(request.POST.get("glasses_max_limit"))
    lockers_max_limit = int(request.POST.get("lockers_max_limit"))
    lockers_min_limit = int(request.POST.get("lockers_min_limit"))
    storage_location = request.POST.get("storage_location")
    is_vender = request.POST.get("is_vender")
    ship_direction = request.POST.get("ship_direction",'')
    return_data = {'code': '', 'message': '', 'dataMsg': ''}
    if ship_direction == 'EXPRESS':
        storage_location='EPS'
    elif ship_direction == 'OM_EXPRESS':
        storage_location='OM-EPS'
    items = None
    logging.debug(ship_direction)
    try:
        # 初始化，如果存在一样的初始化名字进行update，无则save，如果存在，对于增加仓位数量进行累加,生成仓位主表、仓位明细表是仓位号在镜片生产时save
        # 通告位置名称（DY or SH）查找是否存在此配置信息
        with connections['default'].cursor() as cursor:
            sql = """SELECT
                              *
                           FROM
                               wms_lockers_config
                           WHERE
                              storage_location ='%s'
                   """ % storage_location
            lockers_sql = """SELECT
                                         *
                                      FROM
                                          wms_lockers
                                      WHERE
                                         storage_location ='%s'
                              """ % storage_location
            cursor.execute(sql)
            items = namedtuplefetchall(cursor)
            cursor.execute(lockers_sql)
            lockers_items = namedtuplefetchall(cursor)
        if len(items):
            lockersconfig = LockersConfig()
            lockers_config = lockersconfig.query_by_id(items[0].id)
            # 仓位变化差额，必须大于，以防原来仓位已经存有镜片
            old_locker_num = int(lockers_config.lockers_max_limit)
            margin_num = lockers_max_limit - old_locker_num

            if margin_num > 0:
                for lockernum in range(old_locker_num, lockers_max_limit):
                    if lockernum == lockers_max_limit:
                        lockernum = bytes(lockernum)
                    else:
                        lockernum = bytes(lockernum + 1)
                    lockers = Lockers()
                    lockers.storage_location = storage_location
                    lockers.quantity = '0'
                    lockers.locker_num = lockernum
                    lockers.save()

            lockers_config.glasses_max_limit = glasses_max_limit
            lockers_config.lockers_min_limit = lockers_min_limit
            lockers_config.lockers_max_limit = lockers_max_limit
            lockers_config.is_vender = is_vender
            lockers_config.ship_direction = ship_direction
            lockers_config.save()

            logging.debug(lockers_items)
        else:
            lockersconfig = LockersConfig()
            lockersconfig.storage_location = storage_location
            lockersconfig.lockers_max_limit = lockers_max_limit
            lockersconfig.lockers_min_limit = lockers_min_limit
            lockersconfig.glasses_max_limit = glasses_max_limit
            lockersconfig.is_vender = is_vender
            lockersconfig.ship_direction = ship_direction
            lockersconfig.save()

            max_num = int(lockers_max_limit)
            if lockers_min_limit!='':
                lockers_min_limit= int(lockers_min_limit)
            for lockernum in range(lockers_min_limit, max_num+1):
                lockers = Lockers()
                locker_num = bytes(lockernum + 0)
                lockers_number = locker_num
                lockers.storage_location = storage_location
                lockers.quantity = '0'
                lockers.locker_num = lockers_number
                lockers.save()

        return_data['code'] = "200"
        return_data['message'] = "初始化成功"
        return JsonResponse(return_data)

    except Exception as e:
        logging.debug("Error==>%s" % e)
        return_data['code'] = "100"
        return_data['message'] = e
        return JsonResponse(return_data)


# 移除仓位
@login_required
@permission_required('wms.LOCKERS_REMOVE', login_url='/oms/forbid/')
def remove_locker(request):
    return_data = {'code': '', 'message': '', 'dataMsg': ''}
    lab_number = request.POST.get('lab_number')
    logging.debug(lab_number)
    try:
        lab_number = request.POST.get('lab_number')
        lock = locker_controller()
        username = request.user.username
        logging.debug(username)
        rm = lock.deleteItem(lab_number,username)
        logging.debug(rm.code)
        if rm.code == 0:
            return_data['code'] = "200"
            return_data['message'] = rm.message
        else:
            return_data['code'] = "101"
            return_data['message'] = rm.message
        return JsonResponse(return_data)
    except Exception as e:
        logging.debug("Error==>%s" % e)
        return_data['code'] = "100"
        return_data['message'] = e
        return JsonResponse(return_data)


# 仓位VD指定
@login_required
@permission_required('wms.LOCKERS_INIT', login_url='/oms/forbid/')
def locker_vender_set(request):
    return_data = {'code': '', 'message': '', 'dataMsg': ''}
    id = request.POST.get('id')
    vendor = request.POST.get('vendor')
    logging.debug(vendor)
    try:
        lock = locker_controller()
        rm = lock.reset_vendor(id, vendor)
        logging.debug(rm.code)
        if rm.code == 0:
            return_data['code'] = "200"
            return_data['message'] = rm.message
        else:
            return_data['code'] = "101"
            return_data['message'] = rm.message
        return JsonResponse(return_data)
    except Exception as e:
        logging.debug("Error==>%s" % e)
        return_data['code'] = "100"
        return_data['message'] = e
        return JsonResponse(return_data)


# 仓位日志管理
@login_required
@permission_required('wms.LOCKERS_LOG', login_url='/oms/forbid/')
def lockers_log(request):
    _form_data = {}
    lab_number = request.GET.get('lab_number', '')
    page = request.GET.get('page', 1)
    try:
        currentPage = int(page)
        if lab_number !='':
            lockers_log = LockersLog.objects.filter(lab_number=lab_number)
        else:
            lockers_log = LockersLog.objects.filter()
        count = len(lockers_log)
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        if count > 0:
            _form_data['total'] = len(lockers_log)

        paginator = Paginator(lockers_log, 20)  # Show 20 contacts per page

        try:
            lockers_log = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            lockers_log = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            lockers_log = paginator.page(paginator.num_pages)
        return render(request, "laborder_lockers_log.html",
                      {
                          'form_data': _form_data,
                          'lab_number': lab_number,
                          'lockers_log':lockers_log,
                          'paginator': paginator,
                          'currentPage': currentPage,
                          'query_string': query_string,
                          'requestUrl': '/wms/wms_lockers_log/'
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data
                      })


# sku 出入库sku备注信息
@login_required
@permission_required('wms.PRODUCTION_SKU_HISTORY', login_url='/oms/forbid/')
def wms_production_sku_history(request):
    _form_data = {}
    sku = request.GET.get('sku', '')
    type = request.GET.get('type', '')
    page = request.GET.get('page', 1)
    list=''
    try:
        currentPage = int(page)
        if type=="invrs":
            list = inventory_receipt.objects.filter(sku=sku).order_by("-id")
        elif type=="invds":
            list = inventory_delivery.objects.filter(sku=sku).order_by("-id")

        count = len(list)
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        if count > 0:
            _form_data['total'] = len(list)

        paginator = Paginator(list, 20)  # Show 20 contacts per page

        try:
            list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            list = paginator.page(paginator.num_pages)
        return render(request, "inventory_production_sku_history.html",
                      {
                          'form_data': _form_data,
                          'list':list,
                          'sku':sku,
                          'type':type,
                          'paginator': paginator,
                          'currentPage': currentPage,
                          'query_string': query_string,
                          'requestUrl': '/wms/inventory_production_sku_history/'
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data
                      })


@login_required
@permission_required('wms.INVENTORY_DELIVERY_LENS', login_url='/oms/forbid/')
def get_product_lens_sph(request):
    try:
        sph_list = []
        sku = request.GET.get('sku', '')
        sql = """SELECT distinct sph FROM wms_inventory_struct_lens WHERE sku='%s'""" % sku
        with connections['pg_oms_query'].cursor() as conn:
            conn.execute(sql)
            results = namedtuplefetchall(conn)
            for item in results:
                sph_list.append(str(item.sph))
        return json_response(code=0, msg='执行成功', data=sph_list)
    except Exception as e:
        return json_response(code=-1, msg=e, data='')


@login_required
@permission_required('wms.INVENTORY_DELIVERY_LENS', login_url='/oms/forbid/')
def get_product_lens_cyl(request):
    try:
        cyl_list = []
        sku = request.GET.get('sku', '')
        sph = request.GET.get('sph', '')
        sql = """SELECT distinct cyl FROM wms_inventory_struct_lens WHERE sku='%s' AND sph='%s' """ % (sku, sph)
        with connections['pg_oms_query'].cursor() as conn:
            conn.execute(sql)
            results = namedtuplefetchall(conn)
            for item in results:
                cyl_list.append(str(item.cyl))
        return json_response(code=0, msg='执行成功', data=cyl_list)
    except Exception as e:
        return json_response(code=-1, msg=e, data='')


@login_required
@permission_required('merchandising.PRODUCT_MANAGEMENT', login_url='/oms/forbid/')
def redirect_product_management_excel(request):
    '''
    库存列表 V2
    :param request:
    :return:
    '''
    _form_data = {}
    _items = []
    try:
        page = request.GET.get('page', 1)
        sku = request.GET.get('sku', '')
        sort_filter = request.GET.get('sort_filter', 'all')
        _filter = request.GET.get('filter', 'all')
        status_filter = request.GET.get('status_filter', 'all')
        currentPage = int(page)
        with connections['pg_oms_query'].cursor() as cursor:
            sql = '''SELECT
                            t0.id,
                            t0.sku,
                            t1.name,
                            t0.quantity,
                            t0.lock_quantity,
                            t0.reserve_quantity,
                            t0.no_sale_quantity,
                            t0.ch_quantity,
                            t0.al_quantity,
                            t0.retired,
                            t0.estimate_replenishment_date,
                            t0.web_status,
                            t0.web_quantity,
                            t0.oms_web_diff,
                            t0.last_out_of_stock,
                            t0.last_in_stock,
                            t0.last_retired,
                            t0.last_sign,
                            t0.status
                        FROM
                            wms_inventory_struct AS t0
                        LEFT JOIN wms_product_frame AS t1 ON t0.sku = t1.sku '''
            if sku != '':
                sql = sql + ''' WHERE t0.sku LIKE "%%%s%%" ''' % sku
            elif  _filter == 'all':
                sql = sql + ''' WHERE t0.retired <> True '''
            else:
                if _filter.lower() == 'retired':
                    sql = sql + ''' WHERE t0.retired = True '''
                else:
                    sql = sql + ''' WHERE t0.status="%s" AND t0.retired <> True ''' % _filter.upper()


            if sort_filter == '1':
                sql = sql + ''' ORDER BY oms_web_diff '''
                # iiss = iiss.order_by('oms_web_diff')
            elif sort_filter == '2':
                sql = sql + ''' AND quantity <= 50 ORDER BY quantity '''
                # iiss = iiss.filter(quantity__lte=50).order_by('quantity')
            elif sort_filter == '3':
                sql = sql + ''' AND oms_web_diff=0 ORDER BY quantity '''
                # iiss = iiss.filter(oms_web_diff=0).order_by('quantity')
            elif sort_filter == '4':
                sql = sql + ''' AND oms_web_diff<>0 ORDER BY quantity '''
                # iiss = iiss.exclude(oms_web_diff=0).order_by('quantity')
            elif sort_filter == '5':
                sql = sql + '''  ORDER BY al_quantity DESC '''
                # iiss = iiss.order_by('-al_quantity')
            else:
                sql = sql + '''  ORDER BY quantity '''
                # iiss = iiss.order_by('quantity')

            cursor.execute(sql)
            iiss = namedtuplefetchall(cursor)
        for iis in iiss:
            if status_filter == 'status_diff':
                if iis.status != iis.web_status:
                    item = (
                        iis.sku,
                        iis.name,
                        iis.quantity,
                        iis.lock_quantity,
                        iis.reserve_quantity,
                        iis.no_sale_quantity,
                        iis.ch_quantity,
                        iis.al_quantity,
                        iis.retired,
                        iis.status,
                        iis.web_status,
                        iis.web_quantity,
                        iis.oms_web_diff,
                        iis.last_in_stock,
                        iis.last_out_of_stock,
                        iis.last_retired
                    )
            elif status_filter == 'status_same':
                if iis.status == iis.web_status:
                    item = (
                        iis.sku,
                        iis.name,
                        iis.quantity,
                        iis.lock_quantity,
                        iis.reserve_quantity,
                        iis.no_sale_quantity,
                        iis.ch_quantity,
                        iis.al_quantity,
                        iis.retired,
                        iis.status,
                        iis.web_status,
                        iis.web_quantity,
                        iis.oms_web_diff,
                        iis.last_in_stock,
                        iis.last_out_of_stock,
                        iis.last_retired
                    )
            else:
                item = (
                    iis.sku,
                    iis.name,
                    iis.quantity,
                    iis.lock_quantity,
                    iis.reserve_quantity,
                    iis.no_sale_quantity,
                    iis.ch_quantity,
                    iis.al_quantity,
                    iis.retired,
                    iis.status,
                    iis.web_status,
                    iis.web_quantity,
                    iis.oms_web_diff,
                    iis.last_in_stock,
                    iis.last_out_of_stock,
                    iis.last_retired

                )
            _items.append(item)
        headerdata = ["sku", "name", "quantity", "lock_quantity", "reserve_quantity", "no_sale_quantity", "ch_quantity", "al_quantity", "retired",
                      "status", "web_status", "web_quantity", "oms_web_diff", "last_in_stock", "last_out_of_stock",
                      "last_retired"]
        from util.export_excel import ExcelResponse
        excel_response = ExcelResponse()
        file_name = 'product_management'
        response = excel_response.export_excel(file_name, headerdata, _items)
        return response
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


def update_cargo_location(request):
    # location=request.POST.get()
    try:
        item_id = request.POST.get('item_id', '')
        reply_text = request.POST.get('reply_text', '')
        # if item_id == '':
        #     return json_response(code=-1, msg="id 不能为空")
        #     with connections['default'].cursor() as cursor:
        #         update_sql = '''
        #                         UPDATE wms_inventory_struct_warehouse SET `location`='%s'WHERE sku='%s'
        #                     '''% (location)
        #         cursor.execute(update_sql)
        if reply_text == '':
            return json_response(code=-1, msg="内容不能为空")
        inventory_struct_warehouse.objects.filter(id=item_id).update(location=reply_text)
        return json_response(code=0, msg='执行成功')
    except Exception as e:
        return json_response(code=-1, msg=e, data='')


# SKU
@login_required
@permission_required('wms.INVENTORY_FRAME_EDIT', login_url='/oms/forbid/')
def wms_add_edit_product_frame(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    page = request.GET.get('page', 1)
    sku = request.GET.get('sku', '')
    product_type = request.GET.get('product_type', 'all')
    # 获取搜索框参数
    try:
        _filter = {}
        FRAME_TYPE_CHOICES = product_frame.FRAME_TYPE_CHOICES
        frame_type_choices_list = []
        for ftc in FRAME_TYPE_CHOICES:
            sc = {}
            sc['key'] = ftc[0]
            sc['value'] = ftc[1]
            frame_type_choices_list.append(sc)

        YES_OR_NO_CHOICES = product_frame.YES_OR_NO_CHOICES
        yes_or_no_choices_list = []
        for stc in YES_OR_NO_CHOICES:
            sc = {}
            sc['key'] = stc[0]
            sc['value'] = stc[1]
            yes_or_no_choices_list.append(sc)

        PRODUCT_TYPE_CHOICES = product_frame.PRODUCT_TYPE_CHOICES
        product_type_choices_list = []
        for ptc in PRODUCT_TYPE_CHOICES:
            sc = {}
            sc['key'] = ptc[0]
            sc['value'] = ptc[1]
            product_type_choices_list.append(sc)

        FMAT_TYPE_CHOICES = product_frame.FMAT_TYPE_CHOICES
        fmat_type_choices_list = []
        for fmtc in FMAT_TYPE_CHOICES:
            sc = {}
            sc['key'] = fmtc[0]
            sc['value'] = fmtc[1]
            fmat_type_choices_list.append(sc)

        FSHA_TYPE_CHOICES = product_frame.FSHA_TYPE_CHOICES
        fsha_type_choices_list = []
        for fstc in FSHA_TYPE_CHOICES:
            sc = {}
            sc['key'] = fstc[0]
            sc['value'] = fstc[1]
            fsha_type_choices_list.append(sc)


        ETYP_TYPE_CHOICES = product_frame.ETYP_TYPE_CHOICES
        etyp_type_choices_list = []
        for etc in ETYP_TYPE_CHOICES:
            sc = {}
            sc['key'] = etc[0]
            sc['value'] = etc[1]
            etyp_type_choices_list.append(sc)


        if sku != '':
            flag = is_contain_chinese(sku)
            if flag:
                _filter['name__contains'] = sku
            else:
                sku = sku.upper()
                _filter['sku__contains'] = sku

        if product_type !='' and product_type != 'all':
            _filter['product_type'] = product_type

        product_frame_list = product_frame.objects.filter(**_filter).order_by("-id")
        _items = product_frame_list


        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = _items.count()

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_sku_edit.html", {
            'form_data': _form_data,
            'list': _items,
            'frame_type_choices_list':frame_type_choices_list,
            'yes_or_no_choices_list':yes_or_no_choices_list,
            'product_type_choices_list':product_type_choices_list,

            'fmat_type_choices_list':fmat_type_choices_list,
            'fsha_type_choices_list':fsha_type_choices_list,
            'etyp_type_choices_list':etyp_type_choices_list,

            'response_message': rm,
            'requestUrl': reverse('wms_add_edit_product_frame'),
            'query_string': query_string,
            'paginator': paginator,
            'product_type':product_type
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_add_edit_product_frame'),
        })

@login_required
@permission_required('wms.INVENTORY_FRAME_EDIT', login_url='/oms/forbid/')
def wms_edit_product_frame(request):
    # 获取搜索框参数
    try:
        data = {}
        sku = request.POST.get('sku', '')
        pf = product_frame.objects.get(sku=sku)
        data['sku'] = pf.sku
        data['product_num'] = pf.product_num
        data['product_type'] = pf.product_type
        data['name'] = pf.name
        data['frame_type'] = pf.frame_type
        data['sku_specs'] = pf.sku_specs
        data['base_price'] = str(pf.base_price)
        data['width'] = str(pf.fe)
        data['height'] = str(pf.fh)
        data['bridge'] = str(pf.fb)
        data['ed'] = str(pf.ed)
        data['ct'] = str(pf.ct)


        data['r_a'] = str(pf.r_a)
        data['r_b'] = str(pf.r_b)
        data['r_ed'] = str(pf.r_ed)
        # data['r_ed_axis'] = str(pf.r_ed_axis)
        data['r_circ'] = str(pf.r_circ)
        data['r_fcrv'] = str(pf.r_fcrv)
        data['r_ztilt'] = str(pf.r_ztilt)
        data['l_a'] = str(pf.l_a)
        data['l_b'] = str(pf.l_b)
        data['l_ed'] = str(pf.l_ed)
        # data['l_ed_axis'] = str(pf.l_ed_axis)
        data['l_circ'] = str(pf.l_circ)
        data['l_fcrv'] = str(pf.l_fcrv)
        data['l_ztilt'] = str(pf.l_ztilt)
        data['dbl'] = str(pf.dbl)
        data['temple'] = str(pf.temple)
        data['fmat'] = str(pf.fmat)
        data['fsha'] = str(pf.fsha)
        data['etyp'] = str(pf.etyp)

        data['attribute_set'] = str(pf.attribute_set)
        data['frame_width'] = str(pf.frame_width)
        data['is_nose_pad'] = str(pf.is_nose_pad)
        data['is_has_spring_hinges'] = str(pf.is_has_spring_hinges)
        data['is_color_changing'] = str(pf.is_color_changing)
        data['is_variability'] = str(pf.is_variability)
        data['is_already_synchronous'] = str(pf.is_already_synchronous)

        data['comments'] = pf.comments
        return json_response(code=0, msg='Success', data=data)
    except Exception as e:
        return json_response(code=-1, msg=e)

@login_required
@permission_required('wms.INVENTORY_FRAME_EDIT', login_url='/oms/forbid/')
def wms_save_product_frame(request):
    # 获取搜索框参数
    try:
        sku = request.POST.get('sku', '')
        product_num = request.POST.get('product_num', '')
        name = request.POST.get('name', '')
        product_type = request.POST.get('product_type', '')
        frame_type = request.POST.get('frame_type', '')
        sku_specs = request.POST.get('sku_specs', '')
        # base_price = request.POST.get('base_price', '')
        #         # width = request.POST.get('width', '')
        #         # height = request.POST.get('height', '')
        # bridge = request.POST.get('bridge', '')
        # ed = request.POST.get('ed', '')
        # center = request.POST.get('center', '')


        r_a = request.POST.get('r_a', '')
        r_b = request.POST.get('r_b', '')
        r_ed = request.POST.get('r_ed', '')
        # r_ed_axis = request.POST.get('r_ed_axis', '')
        r_circ = request.POST.get('r_circ', '')
        r_fcrv = request.POST.get('r_fcrv', '')
        r_ztilt = request.POST.get('r_ztilt', '')
        l_a = request.POST.get('l_a', '')
        l_b = request.POST.get('l_b', '')
        l_ed = request.POST.get('l_ed', '')
        # l_ed_axis = request.POST.get('l_ed_axis', '')
        l_circ = request.POST.get('l_circ', '')
        l_fcrv = request.POST.get('l_fcrv', '')
        l_ztilt = request.POST.get('l_ztilt', '')
        dbl = request.POST.get('dbl', '')
        temple = request.POST.get('temple', '')
        fmat = request.POST.get('fmat', '')
        fsha = request.POST.get('fsha', '')
        etyp = request.POST.get('etyp', '')
        attribute_set = request.POST.get('attribute_set', '')
        frame_width = request.POST.get('frame_width','')
        is_nose_pad = request.POST.get('is_nose_pad','')
        is_has_spring_hinges = request.POST.get('is_has_spring_hinges','')
        is_color_changing = request.POST.get('is_color_changing','')
        is_variability = request.POST.get('is_variability', '')
        is_already_synchronous = request.POST.get('is_already_synchronous', '')

        comments = request.POST.get('comments', '')
        pf = product_frame.objects.get(sku=sku)
        pf.name = name
        pf.product_num = product_num
        pf.product_type = product_type
        pf.frame_type = frame_type
        pf.sku_specs = sku_specs
        # pf.base_price = base_price
        # pf.fe = width
        # pf.fh = height
        # pf.fb = bridge
        # pf.ed = ed
        # pf.ct = center

        pf.r_a = r_a
        pf.r_b = r_b
        pf.r_ed = r_ed
        # pf.r_ed_axis = r_ed_axis
        pf.r_circ = r_circ
        pf.r_fcrv = r_fcrv
        pf.r_ztilt = r_ztilt
        pf.l_a = l_a
        pf.l_b = l_b
        pf.l_ed = l_ed
        # pf.l_ed_axis = l_ed_axis
        pf.l_circ = l_circ
        pf.l_fcrv = l_fcrv
        pf.l_ztilt = l_ztilt
        pf.dbl = dbl
        pf.temple = temple
        pf.fmat = fmat
        pf.fsha = fsha
        pf.etyp = etyp

        pf.attribute_set = attribute_set
        pf.frame_width = frame_width
        pf.is_nose_pad = is_nose_pad
        pf.is_has_spring_hinges =is_has_spring_hinges
        pf.is_color_changing = is_color_changing
        pf.is_variability = is_variability
        pf.is_already_synchronous = is_already_synchronous

        pf.comments = comments
        pf.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)

@login_required
@permission_required('wms.INVENTORY_FRAME_EDIT', login_url='/oms/forbid/')
def wms_add_product_frame(request):
    # 获取搜索框参数
    try:
        sku = request.POST.get('sku', '')
        product_num = request.POST.get('product_num', '')
        name = request.POST.get('name', '')
        product_type = request.POST.get('product_type', '')
        frame_type = request.POST.get('frame_type', '')
        sku_specs = request.POST.get('sku_specs', '')
        # base_price = request.POST.get('base_price', 0)
        # width = request.POST.get('width', 0)
        # height = request.POST.get('height', 0)
        # bridge = request.POST.get('bridge', 0)
        # ed = request.POST.get('ed', 0)
        # center = request.POST.get('center', 0)

        r_a = request.POST.get('r_a', '')
        r_b = request.POST.get('r_b', '')
        r_ed = request.POST.get('r_ed', '')
        # r_ed_axis = request.POST.get('r_ed_axis', '')
        r_circ = request.POST.get('r_circ', '')
        r_fcrv = request.POST.get('r_fcrv', '')
        r_ztilt = request.POST.get('r_ztilt', '')
        l_a = request.POST.get('l_a', '')
        l_b = request.POST.get('l_b', '')
        l_ed = request.POST.get('l_ed', '')
        # l_ed_axis = request.POST.get('l_ed_axis', '')
        l_circ = request.POST.get('l_circ', '')
        l_fcrv = request.POST.get('l_fcrv', '')
        l_ztilt = request.POST.get('l_ztilt', '')
        dbl = request.POST.get('dbl', '')
        temple = request.POST.get('temple', '')
        fmat = request.POST.get('fmat', '')
        fsha = request.POST.get('fsha', '')
        etyp = request.POST.get('etyp', '')

        attribute_set = request.POST.get('attribute_set', '')
        frame_width = request.POST.get('frame_width', '')
        is_nose_pad = request.POST.get('is_nose_pad', '')
        is_has_spring_hinges = request.POST.get('is_has_spring_hinges', '')
        is_color_changing = request.POST.get('is_color_changing', '')
        is_variability = request.POST.get('is_variability', '')
        is_already_synchronous = request.POST.get('is_already_synchronous', '')

        comments = request.POST.get('comments', '')
        pf_list = product_frame.objects.filter(sku=sku)
        if len(pf_list)>0:
            return json_response(code=-1, msg='该SKU已存在，请修改！')
        else:
            pf = product_frame()
            pf.sku = sku

        pf.name = name
        pf.product_num = product_num
        pf.product_type = product_type
        pf.frame_type = frame_type
        pf.sku_specs = sku_specs
        # pf.base_price = base_price
        # pf.fe = width
        # pf.fh = height
        # pf.fb = bridge
        # pf.ed = ed
        # pf.ct = center

        pf.r_a = r_a
        pf.r_b = r_b
        pf.r_ed = r_ed
        # pf.r_ed_axis = r_ed_axis
        pf.r_circ = r_circ
        pf.r_fcrv = r_fcrv
        pf.r_ztilt = r_ztilt
        pf.l_a = l_a
        pf.l_b = l_b
        pf.l_ed = l_ed
        # pf.l_ed_axis = l_ed_axis
        pf.l_circ = l_circ
        pf.l_fcrv = l_fcrv
        pf.l_ztilt = l_ztilt
        pf.dbl = dbl
        pf.temple = temple
        pf.fmat = fmat
        pf.fsha = fsha
        pf.etyp = etyp
        #
        pf.attribute_set = attribute_set
        pf.frame_width = frame_width
        pf.is_nose_pad = is_nose_pad
        pf.is_has_spring_hinges = is_has_spring_hinges
        pf.is_color_changing = is_color_changing
        pf.is_variability = is_variability
        pf.is_already_synchronous = is_already_synchronous

        pf.comments = comments
        pf.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('wms.INVENTORY_WAREHOUSE_EDIT', login_url='/oms/forbid/')
def wms_add_edit_warehouse(request):
    _form_data = {}  # 回传参数
    _items = []  # 回传列表
    rm = response_message()  # 响应
    # 获取GET参数
    page = request.GET.get('page', 1)
    sku = request.GET.get('sku', '')
    product_type = request.GET.get('product_type', 'all')
    # 获取搜索框参数
    try:
        _filter = {}
        USER_TO_CHOICES = warehouse.USER_TO_CHOICES
        user_to_choices_list = []
        for utc in USER_TO_CHOICES:
            sc = {}
            sc['key'] = utc[0]
            sc['value'] = utc[1]
            user_to_choices_list.append(sc)

        if sku != '':
            flag = is_contain_chinese(sku)
            if flag:
                _filter['name__contains'] = sku
            else:
                sku = sku.upper()
                _filter['code__contains'] = sku

        if product_type !='' and product_type != 'all':
            _filter['used_to'] = product_type

        warehouse_list = warehouse.objects.filter(**_filter).order_by("-id")
        _items = warehouse_list


        # --页码-- 获取URL中除page外的其它参数
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        _form_data['total'] = _items.count()

        paginator = Paginator(_items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)

        return render(request, "inventory_warehouse_edit.html", {
            'form_data': _form_data,
            'list': _items,
            'user_to_choices_list':user_to_choices_list,
            'response_message': rm,
            'requestUrl': reverse('wms_add_edit_warehouse'),
            'query_string': query_string,
            'paginator': paginator,
            'product_type':product_type
        })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'Lens Delivery'
        return render(request, "exceptions.html", {
            'form_data': _form_data,
            'requestUrl': reverse('wms_add_edit_warehouse'),
        })


@login_required
@permission_required('wms.INVENTORY_WAREHOUSE_EDIT', login_url='/oms/forbid/')
def wms_edit_warehouse(request):
    # 获取搜索框参数
    try:
        data = {}
        code = request.POST.get('code', '')
        wh = warehouse.objects.get(code=code)
        data['code'] = wh.code
        data['name'] = wh.name
        data['location'] = wh.location
        if wh.is_sale:
            sale = '1'
        else:
            sale = '0'
        data['is_sale'] = sale
        data['used_to'] = wh.used_to
        data['comments'] = wh.comments
        return json_response(code=0, msg='Success', data=data)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('wms.INVENTORY_WAREHOUSE_EDIT', login_url='/oms/forbid/')
def wms_save_warehouse(request):
    # 获取搜索框参数
    try:
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        used_to = request.POST.get('used_to', '')
        location = request.POST.get('location', '')
        sale = request.POST.get('sale', '')
        comments = request.POST.get('comments', '')
        from django.db import transaction
        with transaction.atomic():
            wh = warehouse.objects.get(code=code)
            wh.name = name
            wh.location = location
            wh.used_to = used_to
            wh.is_sale = sale
            wh.comments = comments
            wh.save()
            if used_to != 'LENS':
                inv_struct_warehous = inventory_struct_warehouse.objects.filter(warehouse_code=code)
                for item in inv_struct_warehous:
                    inv_struct = inventory_struct.objects.get(sku=item.sku)
                    if sale == '1':
                        diff_quantity = inv_struct.no_sale_quantity - item.quantity
                        if diff_quantity < 0:
                            diff_quantity = 0
                        inv_struct.no_sale_quantity = diff_quantity
                        inv_struct.save()
                    else:
                        inv_struct.no_sale_quantity = inv_struct.no_sale_quantity + item.quantity
                        inv_struct.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('wms.INVENTORY_WAREHOUSE_EDIT', login_url='/oms/forbid/')
def wms_add_warehouse(request):
    # 获取搜索框参数
    try:
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        used_to = request.POST.get('used_to', '')
        location = request.POST.get('location', '')
        sale = request.POST.get('sale', '')
        comments = request.POST.get('comments', '')
        wh_list = warehouse.objects.filter(code=code)
        if len(wh_list)>0:
            return json_response(code=-1, msg='该code已存在，请修改！')
        else:
            wh = warehouse()
            wh.code = code

        wh.name = name
        wh.used_to = used_to
        wh.location = location
        wh.is_sale = sale
        wh.comments = comments
        wh.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('wms.RETIRED', login_url='/oms/forbid/')
def edit_no_sale_quantity(request):
    frame_sku = request.POST.get('frame', '')
    no_sale_quantity = request.POST.get('no_sale_quantity', '')
    rm = util.response.response_message.response_dict()

    try:
        invs = inventory_struct.objects.get(sku=frame_sku)
        if no_sale_quantity != '':
            invs.no_sale_quantity = int(no_sale_quantity)
            rm['message'] = no_sale_quantity
        else:
            rm['code'] = '-1'
            rm['message'] = 'ERR==> lock_quantity:%s, frame_sku:%s' % (no_sale_quantity, frame_sku)
            return JsonResponse(rm)

        invs.save()
        # OperationLog log
        ol = OperationLog()
        ol.log(invs.type, invs.id, invs.lock_quantity, "no_sale_quantity", request.user)

    except Exception as e:
        rm['code'] = '-1'
        rm['message'] = str(e).encode('raw_unicode_escape')

    return JsonResponse(rm)

@login_required
@permission_required('wms.RETIRED', login_url='/oms/forbid/')
def file_download(request):
    """ 下载VCA文件 """
    product_num = request.GET.get('product_number', '')


    sql = "SELECT * FROM wms_product_frame_vca WHERE product_num={0};"
    try:
        with connections['pg_oms_query'].cursor() as cursor:
            sql = sql.format(product_num)

            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            if (results.__len__()!=0):
                file_path = results[0].file_path
                name = results[0].product_num

                res = requests.get('http://oms.zhijingoptical.cn/'+file_path)

                response = HttpResponse(res, content_type="application/octet-stream")
                from django.utils.encoding import escape_uri_path

                response['Content-Disposition'] = "attachment; filename={};".format(escape_uri_path(name + '.vca'))
                return response
            else:
                return  json_response(code=-1,msg='文件不存在')
    except Exception as e:
        return ''


