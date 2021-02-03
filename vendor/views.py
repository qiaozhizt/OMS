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

from wms.models import locker_controller

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

from util.response import response_message
import util
import time

from util.dict_helper import *
from util.format_helper import *

from models import lens
from contollers import *

from oms import const
from util.const import *
from api.controllers.tracking_controllers import tracking_lab_order_controller
from oms.models.order_models import LabOrder


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('vendor.LENS', login_url='/oms/forbid/')
def redirect_lens(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            entity = parameters
            parameters = {}
            parameters['entity'] = entity

            lc = lens_contoller()
            rm = lc.get_all(parameters)
            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            return HttpResponse(json_body)

        lc = lens_contoller()
        rm = lc.get_all(parameters)
        _form_data['list'] = rm.obj
        # 获取页码
        page = request.GET.get('page', 1)
        # 获取URL中除page外的其它参数
        import re
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        # 分页对象，设置每页20条数据
        paginator = Paginator(_form_data['list'], 20)

        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            contacts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            contacts = paginator.page(paginator.num_pages)
    except Exception as e:
        rm.capture_execption(e)
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)

    return render(
        request, "lens_all.html",
        {
            "form": _form_data,
            'list': contacts,
            'paginator': paginator,
            'query_string': query_string,
        }
    )


@login_required
@permission_required('vendor.LENS', login_url='/oms/forbid/')
def redirect_lens_by_lbo(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            logging.debug('收到请求 ....')
            entity = parameters
            parameters = {}
            lab_number = request.POST.get('lab_number', '')
            lbo = LabOrder.objects.get(lab_number=lab_number)
            parameters['lbo'] = lbo
            parameters['lens_sku'] = request.POST.get('base_sku', '')
            vendor = request.POST.get('vendor', '')
            if vendor == '2':
                vendor = '3'

            if vendor == '0':
                vendor = ''
            parameters['vendor'] = vendor

            logging.debug(parameters['vendor'])

            rm_req = response_message()
            rm_req.obj = parameters

            lc = lens_contoller()
            rm = lc.get_by_lbo(rm_req)

            objs = rm.obj
            vendor_lens_list = []

            for obj in objs:
                vendor_lens = {}
                vendor_lens['sku'] = obj.sku
                vendor_lens['name'] = obj.name
                vendor_lens_list.append(vendor_lens)

                logging.debug(obj.sku)

            rm.obj = vendor_lens_list
            json_body = dh.convert_to_dict(rm)
            logging.debug(json_body)
            json_body = json.dumps(json_body, cls=DateEncoder)

            logging.debug(json_body)
            return HttpResponse(json_body)

        lc = lens_contoller()
        rm = lc.get_all(parameters)
        _form_data['list'] = rm.obj
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


@login_required
@permission_required('vendor.LENS', login_url='/oms/forbid/')
def redirect_lens_by_vd(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            logging.debug('收到请求 ....')

            logging.debug(AUTHOR)
            entity = parameters
            parameters = {}
            vendor = request.POST.get('vendor', '')
            index = request.POST.get('index', '')
            if vendor == '2':
                vendor = '3'

            if vendor == '0':
                vendor = ''

            if vendor == '9':
                vendor = '5'
            parameters['vendor'] = vendor
            parameters['index'] = index

            rm_req = response_message()
            rm_req.obj = parameters

            lc = lens_contoller()
            rm = lc.get_by_vd(rm_req)

            objs = rm.obj
            vendor_lens_list = []

            for obj in objs:
                vendor_lens = {}
                vendor_lens['sku'] = obj.sku
                vendor_lens['name'] = obj.name
                vendor_lens_list.append(vendor_lens)

                logging.debug(obj.sku)

            rm.obj = vendor_lens_list
            json_body = dh.convert_to_dict(rm)
            logging.debug(json_body)
            json_body = json.dumps(json_body, cls=DateEncoder)

            logging.debug(json_body)
            return HttpResponse(json_body)

        lc = lens_contoller()
        rm = lc.get_all(parameters)
        _form_data['list'] = rm.obj
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


@login_required
@permission_required('vendor.LENS_ORDER', login_url='/oms/forbid/')
def redirect_lens_orders(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        page = request.GET.get('page', 1)
        currentPage = int(page)
        loc = lens_order_contoller()
        rm = loc.get_all(parameters)

        items = rm.obj
        _form_data['list'] = items
        _form_data['total'] = rm.count

        paginator = Paginator(items, 20)  # Show 20 contacts per page
        # 获取URL中除page外的其它参数
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


    except Exception as e:
        rm.capture_execption(e)
        # json_body = dh.convert_to_dict(rm)
        # json_body = json.dumps(json_body, cls=DateEncoder)
        # return HttpResponse(json_body)

    return render(
        request, "lens_orders.html",
        {
            "form": _form_data,
            'list': items,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': reverse('lens_orders'),
            'query_string': query_string,
        }
    )


@login_required
@permission_required('vendor.LENS_ORDER', login_url='/oms/forbid/')
def redirect_lens_order_new(request, parameters=''):
    _form_data = {}
    _items = []
    rm = response_message()
    rm.code = 0
    dh = dict_helper()

    try:
        rm.obj = 'ok'

        lab_number = request.POST.get('lab_number', '')

        paras = {}
        paras['pa'] = parameters

        paras['user'] = request.user

        lbo = LabOrder.objects.get(lab_number=lab_number)
        paras['lbo'] = lbo

        loc = lens_order_contoller()
        loc.create(paras)

    except Exception as e:
        _rm.capture_execption(e)

    json_body = dh.convert_to_dict(rm)
    json_body = json.dumps(json_body, cls=DateEncoder)
    return HttpResponse(json_body)


@login_required
@permission_required('vendor.LAB_ORDER_DISTRIBUTE', login_url='/oms/forbid/')
def redirect_distribute_lab_orders(request, parameters=''):
    _form_data = {}
    _items = []
    rm = response_message()
    rm.code = 0
    dh = dict_helper()

    try:
        rm.obj = 'ok'

        lab_number = request.POST.get('lab_number', '')

        paras = {}
        paras['pa'] = parameters

        paras['user'] = request.user

        lbo = LabOrder.objects.get(lab_number=lab_number)
        paras['lbo'] = lbo

        dc = distribute_controller()
        rm = dc.distribute_vendor(lbo, paras)

    except Exception as e:
        _rm.capture_execption(e)

    json_body = dh.convert_to_dict(rm)
    json_body = json.dumps(json_body, cls=DateEncoder)
    return HttpResponse(json_body)


@login_required
# @permission_required('vendor.LAB_ORDER_DISTRIBUTE', login_url='/oms/forbid/')
def redirect_distribute_lab_orders_manual(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            logging.debug('收到请求 ....')
            logging.debug(AUTHOR)

            parameters = {}

            parameters['request'] = request

            lab_number = request.POST.get('lab_number', '')
            vendor = request.POST.get('vendor', '')
            lens_sku = request.POST.get('lens_sku', '')
            lens_name = request.POST.get('lens_name', '')
            logging.debug('lab_number: %s' % lab_number)
            lbo = LabOrder.objects.get(lab_number=lab_number)
            logging.debug(vendor)
            logging.debug(lbo.status)
            if vendor in ['1000', '1001']:
                if (lbo.status == 'SHIPPING' or lbo.status == 'DELIVERED' or lbo.status == 'CANCELLED' or lbo.status == 'CLOSED'):
                    rm.code = -3
                    rm.message = '当前状态是【%s】不允许修改VD' % lbo.status
                    json_body = dh.convert_to_dict(rm)
                    json_body = json.dumps(json_body, cls=DateEncoder)
                    return HttpResponse(json_body)
                lbo.vendor = vendor
                lbo.save()
                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, request.user, 'MANUAL', '手动分单', '手动分单vd'+vendor)
                json_body = dh.convert_to_dict(rm)
                json_body = json.dumps(json_body, cls=DateEncoder)
                return HttpResponse(json_body)
            else:
                parameters['lbo'] = lbo
                parameters['lab_number'] = lab_number
                parameters['modify'] = 'MANUAL'
                parameters['vendor'] = vendor
                parameters['lens_sku'] = lens_sku
                parameters['lens_name'] = lens_name
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

        lc = lens_contoller()
        rm = lc.get_all(parameters)
        _form_data['list'] = rm.obj
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


@login_required
@permission_required('vendor.SET_WC_LENS', login_url='/oms/forbid/')
def set_wc_lens_from_json(request):
    # 响应参数
    rm = {}
    form_data = {}
    # 参数初始化
    rm['code'] = 0
    if request.method == 'POST':
        # 获取请求数据
        lens_code_str = request.POST.get('lens_code_str', '')
        product_str = request.POST.get('product_str', '')
        material_str = request.POST.get('material_str', '')
        imbd_str = request.POST.get('imbd_str', '')
        # str转字典
        lens_code_json = json.loads(lens_code_str)
        product_json = json.loads(product_str)
        material_json = json.loads(material_str)
        imbd_json = json.loads(imbd_str)
        try:
            logging.debug('开始')
            # 遍历写入lens_code信息
            for item in lens_code_json:
                new_wc_lens = wc_lens()
                new_wc_lens.code = item['Lens_Code']
                new_wc_lens.index = float(item['aIndex'])
                new_wc_lens.product_sku = item['products']
                new_wc_lens.material_sku = item['material']
                new_wc_lens.save()

            logging.debug('写lens_code完成')
            # 重新查询 遍历其它JSON，根据条件填充剩余参数
            wc_lens_entity = wc_lens.objects.all()
            # 写product参数
            for item in product_json:
                product_sku = item['Products']
                product_name = item['P_HZ']
                product_can_add = False
                if item['Add_YN'] == 'True':
                    product_can_add = True
                product_channel_range = item['Channel']
                product_assemble_height_range = item['Min_ZpHeight']
                wc_lens_entity_part = wc_lens_entity.filter(product_sku=product_sku)
                wc_lens_entity_part.update(product_name=product_name,product_can_add=product_can_add
                                           ,product_channel_range=product_channel_range
                                           ,product_assemble_height_range=product_assemble_height_range)

            logging.debug('写product完成')
            # 写material参数
            for item in material_json:
                material_sku = item['Material']
                material_name = item['M_HZ']
                wc_lens_entity_part = wc_lens_entity.filter(material_sku=material_sku)
                wc_lens_entity_part.update(material_name=material_name)
            logging.debug('写material完成')

            # 写IMBD参数
            for item in imbd_json:
                index = item['aIndex']
                material_sku = item['material']
                diamater = item['ZJ']
                base_bending = item['Base']
                wc_lens_entity_part = wc_lens_entity.filter(index=index,material_sku=material_sku)
                wc_lens_entity_part.update(diamater=diamater,base_bending=base_bending)
            logging.debug('写IMBD完成')

            rm['message'] = '成功!'
            rm_js = json.dumps(rm)
            return HttpResponse(rm_js)
        except Exception as e:
            logging.debug(str(e))
            rm['code'] = -1
            rm['message'] = str(e)
            rm_js = json.dumps(rm)
            return HttpResponse(rm_js)

    # GET
    return render(
        request, 'set_wc_lens.html',
        {'form_data': form_data}
    )
