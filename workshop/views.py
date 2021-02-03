# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.core import paginator
from django.shortcuts import render
import logging
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from util.response import response_message
from django.http import HttpResponse, JsonResponse
import simplejson as json

from django.http import HttpResponseRedirect
from workshop.models import assembled_control,assembling_control
from oms.controllers.lab_order_controller import lab_order_controller, laborder_request_notes
from oms.models.order_models import LabOrder
from api.controllers.tracking_controllers import tracking_lab_order_controller
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from oms import const
from qc.models import lens_registration_control, preliminary_checking_control
from wms.models import locker_controller, product_frame
from util.dict_helper import *
from vendor.contollers import distribute_controller, lens_contoller
from util.format_helper import DateEncoder


@login_required
@permission_required('workshop.ASSEMBLED', login_url='/oms/forbid/')
def redirect_assembled(request):
    '''
    装配完成
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'ASSEMBLED'
    items = []
    lbo = None

    try:
        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')

            if lab_number == '':
                res['code'] = -1
                res['message'] = '请输入订单号!!'
                return HttpResponse(json.dumps(res))
            try:
                cac = assembled_control()
                # add 中已做事务处理
                rm = cac.add(
                    request,
                    lab_number
                )

                res['code'] = rm.code
                res['message'] = rm.message

                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, request.user, "ASSEMBLING", "装配完成")

            except Exception as e:
                res['code'] = -999
                res['message'] = '数据遇到异常: ' + e.message

            return HttpResponse(json.dumps(res))

        entity_id = request.GET.get('entity_id', '')
        # _form_data["search_entity"] = entity_id

        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            # 用来到wms_product_frame中查找sku_specs字段（警示信息）
            caution_info = product_frame.objects.get(sku=lbo.frame)
            _form_data['caution_info'] = caution_info.sku_specs

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

        return render(request, "assembled.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_assembled'),
                          'item': lbo,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_assembled'),
                      })


@login_required
@permission_required('workshop.ASSEMBLING', login_url='/oms/forbid/')
def redirect_assembling(request):
    '''
    装配完成
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}
    _page_info = {}
    page = request.GET.get('page', 1)
    currentPage = int(page)
    paginator = None
    items = []
    lbo = None
    # 装配中订单添加VD9
    vendors_choice_list = []
    vendor = request.GET.get('vendor', 'all')
    # 用户名前两个字符
    prefix = request.user.username[0:2]
    # wx用户选其它VD 都默认为VD5
    if prefix == 'wx' and not (vendor == '5' or vendor == '9'):
        vendor = '5'
    for vcl in LabOrder.VENDOR_CHOICES:
        vc = status_choice()
        vc.key = vcl[0]
        vc.value = vcl[1]
        if int(vc.key) > 0 and int(vc.key) <= 10:
            vendors_choice_list.append(vc)
        target_day = const.date_delta()
        logging.debug(target_day)
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    try:
        filter_vendor = {}
        filter_vendor['vendor'] = vendor
        ac = assembling_control()
        items = ac.get_items(filter_vendor)
        if sorted == 'set_time':
            paginator = Paginator(items)
        else:
            paginator = Paginator(items, const.PAGE_SIZE_MORE)  # Show 20 contacts per page
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)
        if request.method == 'POST':
            return HttpResponse("ok")

        return render(request, "assembling.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_assembling'),
                          'list': items,
                          'page_info': _page_info,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'vendors_choices': vendors_choice_list,
                          'query_string': query_string,
                          'vendor': vendor,
                          'prefix': prefix,
                      })

    except Exception as e:
        logging.debug('Exception: %s' % e)
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'requestUrl': reverse('workshop_assembling'),
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'vendor': vendor,
                      })


class status_choice:
    key = ''
    value = ''
    permission = ''
    switch = 0

@login_required
@permission_required('workshop.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_glasses_return(request):
    '''
    装配完成
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}
    _page_info = {}

    _form_data['request_feature'] = 'GLASSES_RETURN'
    items = []
    lbo = None

    try:
        entity_id = request.GET.get('entity_id', '')

        page = request.GET.get('page', 1)
        currentPage = int(page)

        filter_ext = {}
        filter_ext['status'] = 'GLASSES_RETURN'
        filter_ext['vendor'] = 5

        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                _id = lbo.lab_number
            else:
                _id = entity_id

            filter_ext['lab_number'] = _id

        ac = assembling_control()
        items = ac.get_items(filter_ext)
        count = len(items)

        if count > 0:
            _form_data['total'] = count
            _page_info['total'] = count

        if sorted == 'set_time':
            paginator = Paginator(items, count)
        else:
            paginator = Paginator(items, const.PAGE_SIZE_MORE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)
        if request.method == 'POST':
            return HttpResponse("ok")

        return render(request, "glasses_return.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_glasses_return'),
                          'list': items,
                          'page_info': _page_info,
                          'currentPage': currentPage, 'paginator': paginator,
                          'filter': filter,
                      })

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_glasses_return'),
                      })


@login_required
@permission_required('oms.CVFG_QUICK_VIEW', login_url='/oms/forbid/')
def redirect_construction_voucher_finished_glasses_quick(request):
    '''

    :param request:
    :return:
    '''
    _form_data = {}
    _form_data['request_feature'] = 'Finished Glasses'
    _items = []
    _paginator = None
    _id = -1
    try:
        return render(request, "construction_voucher_finished_glasses_quick.html",
                      {
                          'form_data': _form_data,
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
@permission_required('qc.LENS_REGISTRATION', login_url='/oms/forbid/')
def redirect_lens_registration_quick(request):
    '''
    来片登记快捷
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}  # 字典，相当于hashMap
    _form_data['code'] = 0
    _form_data['request_feature'] = 'Lens Registration'
    items = []
    lbo = None
    try:
        # if request.method == 'POST':
        #     res = {}
        #     lab_number = request.POST.get('lab_nubmer', '')
        #
        #     if lab_number == '':
        #         res['code'] = -1
        #         res['message'] = '请输入订单号!!'
        #         _form_data['code'] = -1
        #         _form_data['message'] = '请输入订单号!!'
        #         return HttpResponse(json.dumps(res))
        #
        #     try:
        #         logging.debug('----------------------------------------')
        #         lrc = lens_registration_control()
        #         # lens_registration_control.add 已添加事务
        #         rm = lrc.add(
        #             request,
        #             lab_number
        #         )
        #         res['code'] = rm.code
        #         res['message'] = rm.message
        #         logging.debug('----------------------------------------')
        #
        #     except Exception as e:
        #         res['code'] = -999
        #         res['message'] = '数据遇到异常: ' + e.message
        #         _form_data['code'] = -1
        #         _form_data['message'] = '数据遇到异常: ' + e.message
        #     return HttpResponse(json.dumps(res))
        entity_id = request.GET.get('entity_id', '')
        if entity_id == '':
            _form_data['code'] = -1
            _form_data['message'] = '请输入订单号!!'
            return render(request, "construction_voucher_finished_glasses_quick.html",
                          {
                              'form_data': _form_data,
                              'requestUrl': reverse('workshop_lens_registration_quick'),
                          })

        loc = lab_order_controller()
        lbos = loc.get_by_entity(entity_id)

        if len(lbos) == 1:
            lbo = lbos[0]
            lab_number = lbo.lab_number

        # 用来到wms_product_frame中查找sku_specs字段（警示信息）
        caution_info = product_frame.objects.get(sku=lbo.frame)
        _form_data['caution_info'] = caution_info.sku_specs

        try:
            logging.debug('----------------------------------------')
            lrc = lens_registration_control()
            # lens_registration_control.add 已添加事务
            rm = lrc.add(
                request,
                lab_number
            )
            if rm.code == 0:
                _form_data['message'] = "【来片登记】操作成功！"
            else:
                _form_data['code'] = rm.code
                _form_data['message'] = rm.message
            logging.debug('----------------------------------------')

        except Exception as e:
            _form_data['code'] = -1
            _form_data['message'] = '数据遇到异常: ' + e.message

        lbo = LabOrder.objects.get(lab_number=lab_number)
        _form_data['laborder'] = lbo
        special_handling = lbo.special_handling if lbo.special_handling else ''
        _form_data['special_handling'] = special_handling.replace("\n", "").replace("\t", "").replace("\r", "")
        return render(request, "construction_voucher_finished_glasses_quick.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('workshop_lens_registration_quick'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['code'] = -1
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_lens_registration_quick'),
                      })


@login_required
@permission_required('qc.PRELIMINARY_CHECKING', login_url='/oms/forbid/')
def redirect_preliminary_checking_quick(request):
    '''
    初检快捷
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Preliminary Checking'
    items = []

    lbo = None

    try:
        if request.method == 'POST':
            res = {}

            lab_number = request.POST.get('lab_nubmer', '')
            qualified = request.POST.get('qualified', '')
            reason_code = request.POST.get('reason_code', '')
            reason = request.POST.get('reason', '')
            act_lens_sku = request.POST.get('act_lens_sku', '')
            act_lens_name = request.POST.get('act_lens_name', '')

            if lab_number == '':
                res['code'] = -1
                res['message'] = '请输入订单号!!'
                return HttpResponse(json.dumps(res))

            if qualified == '':
                res['code'] = -1
                res['message'] = '无质检结果信息!!'
                return HttpResponse(json.dumps(res))

            try:
                logging.debug('----------------------------------------')
                if qualified == '1':
                    is_qualified = True
                else:
                    is_qualified = False

                pcc = preliminary_checking_control()
                # preliminary_checking_control.add 已加事务
                rm = pcc.add(
                    request,
                    lab_number,
                    is_qualified,
                    reason_code,
                    reason,
                    act_lens_sku,
                    act_lens_name,
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

        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo
            _form_data['code'] = 0
            if lbo.status == 'LENS_RECEIVE':
                _form_data['message'] = '当前状态为【镜片收货】'
            else:
                _form_data['message'] = '当前状态为【镜片退货】'

        return render(request, "construction_voucher_finished_glasses_quick.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('workshop_preliminary_checking_quick'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('workshop_preliminary_checking_quick'),
                      })

@login_required
@permission_required('oms.CVFG_QUICK_VIEW', login_url='/oms/forbid/')
def redirect_construction_voucher_finished_glasses_quick_submit(request):
    _form_data = {}
    _form_data['request_feature'] = 'Finished Glasses'
    _items = []
    _paginator = None
    _id = -1

    _id = request.GET.get('id', -1)
    logging.debug('id: %s' % _id)

    _form_data['id'] = _id
    try:
        if _id != -1:
            loc = lab_order_controller()
            lbos = loc.get_by_entity(_id)
            lbo = lbos[0]
            lab_number = lbo.lab_number

            if not lbo.status == 'LENS_RECEIVE' and not lbo.status == 'GLASSES_RETURN' and not lbo.status == 'COLLECTION' and not lbo.status == 'ASSEMBLING' and lbo.quantity == 1:
                _form_data['code'] = -1
                _form_data['message'] = "订单只有 镜片收货或成镜返工 状态，才能更改状态!当前订单状态为{0}".format(lbo.status)
                _form_data['laborder'] = lbo
                return render(request, "construction_voucher_finished_glasses_quick.html",
                              {
                                  'form_data': _form_data,
                              })
            elif lbo.status == 'ASSEMBLING':
                _form_data['code'] = -1
                _form_data['message'] = "该订单已是待装配状态！"
                _form_data['laborder'] = lbo
                _form_data['flag'] = 0
                return render(request, "construction_voucher_finished_glasses_quick.html",
                              {
                                  'form_data': _form_data,
                              })

            if lbo.is_production_change:
                _form_data['message'] = "制作参数已经修改，请补打印作业单"
                _form_data['flag'] = 0
                _form_data['code'] = 0
            elif lbo.is_production_change == False:
                lbo.status = 'ASSEMBLING'
                lbo.save()
                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, request.user, 'ASSEMBLING')
                _form_data['code'] = 0
                _form_data['message'] = "【装配】操作成功！"

            # 移除仓位
            lc = locker_controller()
            lc.deleteItem(lab_number)

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo
        return render(request, "construction_voucher_finished_glasses_quick.html",
                      {
                          'form_data': _form_data,
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
# @permission_required('vendor.LAB_ORDER_DISTRIBUTE', login_url='/oms/forbid/')
def redirect_distribute_lab_orders_manual_quick(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            logging.debug('收到请求 ....')

            parameters = {}

            parameters['request'] = request

            lab_number = request.POST.get('lab_number', '')

            logging.debug('lab_number: %s' % lab_number)
            lbo = LabOrder.objects.get(lab_number=lab_number)
            parameters['lbo'] = lbo
            parameters['lab_number'] = lab_number
            parameters['modify'] = 'MANUAL'
            parameters['vendor'] = request.POST.get('vendor', '')
            parameters['lens_sku'] = request.POST.get('lens_sku', '')
            parameters['lens_name'] = request.POST.get('lens_name', '')
            parameters['user'] = request.user

            qualified = request.POST.get('qualified', '')
            if qualified == '1':
                is_qualified = True
            else:
                is_qualified = False

            if is_qualified:
                parameters['qualified'] = is_qualified

            logging.debug('lens_name: %s' % parameters['lens_name'])
            logging.debug(parameters)

            dc = distribute_controller()
            rm = dc.distribute_vendor_manual(parameters)
            logging.debug(rm.code)

            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            logging.debug(json_body)
            return HttpResponse(json_body)
        else:
            lab_number = request.GET.get('lab_number', '')
            qualified = request.GET.get('qualified', '')
            # lc = lens_contoller()
            # rm = lc.get_all(parameters)
            # _form_data['list'] = rm.obj
            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo
            if qualified == '1':
                _form_data['code'] = 0
                _form_data['message'] ="【初检合格】操作成功！"
            else:
                _form_data['code'] = 0
                _form_data['message'] ="【初检不合格】操作成功！"

            return render(request, "construction_voucher_finished_glasses_quick.html",
                      {
                          'form_data': _form_data,
                      })

    except Exception as e:
        rm.capture_execption(e)
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)

    return render(
        request, "lens_all.html",
        {
            "form": _form_data
        }
    )
