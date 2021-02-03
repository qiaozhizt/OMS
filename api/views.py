# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
# import simplejson as json
import json
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from util.response import response_message
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
from django.db.models import Q
import math

from django.contrib.auth import get_user_model

from util.response import response_message
from oms.controllers.pg_order_controller import pg_order_controller

User = get_user_model()
from pg_oms import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission
from util.db_helper import *
from util.dict_helper import *
from util.send_email import SendEmail
import pytz
import urllib2
import requests
import time
import datetime
import oms.const
from api.authcode import AuthCode
from oms.const import *
from oms.models.order_models import LabOrder, PgOrder, PgOrderItem, PgOrderInvoice,RemakeOrder,RemakeOrderCart
from .models import *
from oms.models.utilities_models import utilities, DateEncoder

from oms.controllers.order_controller import PgOrderController
from oms.controllers.lab_order_controller import lab_order_controller
from api.controllers.tracking_controllers import tracking_lab_order_controller
from qc.models import prescripiton_actual
from qc.models import glasses_final_inspection
from qc.models import glasses_final_inspection_technique
from qc.models import laborder_accessories
from qc.models import laborder_accessories_controller
from qc.models import glasses_final_inspection_controller

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.json_response import JsonResponse
from rest_framework.reverse import reverse
from django.http import Http404
from wms.models import inventory_receipt_lens_controller
from wms.models import inventory_operation_log
from wms.models import inventory_struct,product_frame
from oms.models.order_models import PgProduct, LabProduct
from api.serializers import PgOrderItem_IsHasImgsSerializers
from qc.serializers import LaborderAccessoriesSerializers
from oms.serializers import LabOrderSerializers

from django.forms.models import model_to_dict
from shipment.serializers import ShipmentHistorySerializers
from util.search_leaves import SearchLeaves,dict_generator
import requests.packages.urllib3
import urllib
import phpserialize

from vendor.models import corp_apps_info,wc_order_status
from vendor.contollers import WcOrderStatusController
from collections import OrderedDict
from wms.models import ProductFrameVca, HistoryFrameVca
requests.packages.urllib3.disable_warnings()


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


class OrdersStatusRenew(APIView):
    def get(self, request, format=None):
        return HttpResponse('Get method is not support!')

    def post(self, request, format=None):
        rm = response_message()
        try:
            corp_id = request.data['authentication']['corp_id']
            app_key = request.data['authentication']['app_key']
            app_secret = request.data['authentication']['app_secret']

            rm = self.__auth(corp_id, app_key, app_secret)

            if not rm.code ==0:
                return JsonResponse(data=request.data,
                                    code=rm.code,
                                    msg=rm.message,
                                    status=status.HTTP_400_BAD_REQUEST)

            data = request.data.get('data', None)

            if not data:
                return JsonResponse(data=request.data,
                                    code=8001,
                                    msg='payload data deletion!',
                                    status=status.HTTP_400_BAD_REQUEST)

            obc = WcOrderStatusController()
            obc.new(request,data)
        except Exception as ex:
            return JsonResponse(data=str(ex),
                                code=status.HTTP_400_BAD_REQUEST,
                                msg=str(ex),
                                status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data='', code=status.HTTP_200_OK, msg="Success", status=status.HTTP_200_OK)

    def __auth(self, corp_id,app_key,app_secret):
        rm = response_message()
        try:
            cai = corp_apps_info.objects.get(corp_id=corp_id,
                                             app_key=app_key,
                                             app_secret=app_secret)
            rm.code = 0
            rm.message = 'Ok'
        except Exception as ex:
            rm.code = 8099
            rm.message = 'invalid company or app key has been expired!'

        return rm

@csrf_exempt
def redirect_laborders_query(request, params=''):
    res = {}
    res['order_number'] = 0
    res['message'] = ''
    try:
        order_number = params

        loc = lab_order_controller()
        lbos = loc.get_by_entity(order_number)

        if not lbos == None:

            lbo = lbos[0]
            logging.debug(lbo.lab_number)
            lbo_dict = utilities.convert_to_dict(lbo)
            lab_number_list = lbo_dict['lab_number'].split("-")
            new_lab_number = "-".join(lab_number_list[:3])
            pgis = PgOrderItem.objects.filter(lab_order_number=new_lab_number)
            lbo_dict['attribute_set_id'] = ''
            lbo_dict['attribute_set_name'] = ''
            lbo_dict['status_cn'] = lbo.get_status_display()
            # add lee 2020.8.26 ....
            p=product_frame.objects.get(sku__exact=lbo_dict["frame"])
            lbo_dict['is_variability'] = p.is_variability
            # end

            if len(pgis) > 0:
                pgi = pgis[0]
                lbo_dict['attribute_set_id'] = pgi.attribute_set_id
                lbo_dict['attribute_set_name'] = pgi.attribute_set_name
            lbo_json = json.dumps(lbo_dict, cls=DateEncoder)
            # lbo_json =  serializers.serialize('json', lbo)

            return HttpResponse(lbo_json)
        else:
            res['order_number'] = -2
            res['message'] = 'query result incorrect.'
            json_body = json.dumps(res, cls=DateEncoder)
            return HttpResponse(json_body)
    except Exception as e:
        rvalue = '{"exception":"' + e.message + '"}'
        res['order_number'] = -1
        res['message'] = rvalue
        json_body = json.dumps(res, cls=DateEncoder)
        return HttpResponse(json_body)


@csrf_exempt
def redirect_pg_orders_query(request, params=''):
    res = {}
    res['order_number'] = 0
    res['message'] = ''
    try:
        order_number = params
        pg_orders = PgOrder.objects.filter(order_number=order_number)
        logging.critical(PgOrder.objects.filter(order_number=order_number).query)

        if pg_orders.count() == 1:
            pg_order = pg_orders[0]
            # add lee 2020.11.20 pg_order订单用户名
            pg_order.customer_name=str(pg_order.firstname).strip()+" "+str(pg_order.lastname).strip()
            # end
            pg_order_dict = utilities.convert_to_dict(pg_order)
            json_body = json.dumps(pg_order_dict, cls=DateEncoder)
            return HttpResponse(json_body)
        else:
            res['order_number'] = -2
            res['message'] = 'query result incorrect.'
            json_body = json.dumps(res, cls=DateEncoder)
            return HttpResponse(json_body)

    except Exception as e:
        rvalue = '{"exception":"' + e.message + '"}'
        res['order_number'] = -1
        res['message'] = rvalue
        json_body = json.dumps(res, cls=DateEncoder)
        return HttpResponse(json_body)


@csrf_exempt
def redirect_pgorder_address_verified(request):
    try:
        entities = request.POST.get('entities', '')
        logging.debug(entities)
        poc = PgOrderController()
        return poc.pgorder_address_verified(entities)
    except Exception as e:
        return HttpResponse(e.message)


@csrf_exempt
def address_verified(request, res_address):
    resp = 'error'
    if request.method == 'POST':

        req_url = settings.EASYPOST_BASE_URL + settings.EASYPOST_ADDRESS
        logging.debug("req_url==>%s" % req_url)

        http_headers = {
            'Authorization': 'Bearer ' + settings.EASYPOST_API_KEY,
            'Content-Type': 'application/json'
        }

        logging.debug("http_headers==>%s" % http_headers)
        send_data = {
            "verify": ['delivery'],
            "address": res_address
        }

        send_data = json.dumps(send_data)
        logging.debug(send_data)

        try:
            # req = urllib2.Request(url=req_url, data=send_data, headers=http_headers)
            # res = urllib2.urlopen(req)
            req = requests.post(url=req_url, data=send_data, headers=http_headers,timeout=60, verify=False)
            resp = req.text
            # resp = res.read()

            logging.debug(resp)

            res_json = json.loads(resp)

            verifications = res_json.get('verifications', '')

            delivery = verifications.get('delivery', '')
            success = delivery.get('success', '')
            logging.debug('verifications: %s' % verifications)
            logging.debug('success: %s' % success)

            return verifications
        except Exception as e:
            logging.exception(str(e))


@csrf_exempt
def address_verified_api(request):
    json_data = {}
    json_body = json.loads(request.body)
    try:
        request_body = json_body.get('request_body', '')
        logging.debug('request_body: %s' % request_body)

        verifications = ''

        if not request_body == '':
            req_addr = response_address()
            req_addr.street1 = request_body.get('street1', '')
            req_addr.street2 = request_body.get('street2', '')
            req_addr.city = request_body.get('city', '')
            req_addr.state = request_body.get('state', '')
            req_addr.zip = request_body.get('zip', '')
            req_addr.phone = request_body.get('phone', '')

            req_addr = utilities.convert_to_dict(req_addr)
            verifications = address_verified(request, req_addr)
            json_data['code'] = 0
            json_data['message'] = 'Success'

            json_data['request_body'] = json_body
            json_data['response_body'] = verifications
        else:
            json_data['code'] = -1
            json_data['message'] = 'No Data'

            json_data['request_body'] = json_body

        json_data = json.dumps(json_data)
        return HttpResponse(json_data)
    except Exception as e:
        logging.exception(e.message)
        json_data['code'] = -8000
        json_data['message'] = e.message
        json_data['request_body'] = json_body

        json_data = json.dumps(json_data)

        return HttpResponse(json_data)


@csrf_exempt
def redirect_pgorder_address_verified_google(request):
    try:
        entities = request.POST.get('entities', '')
        logging.debug(entities)

        entities = json.loads(entities)

        logging.debug(entities)

        for entity in entities:
            logging.debug(entity)

            sql = oms.const.sql_generate_pg_orders + oms.const.sql_generate_pg_orders_spe

            with connections["pg_mg_query"].cursor() as cursor:
                cursor.execute(sql, [entity])
                results = namedtuplefetchall(cursor)
                result = results[0]

                po = PgOrder.objects.get(order_number=entity)

                updated_at = result.updated_at
                web_updated_at = po.web_updated_at

                # if not po.web_updated_at == result.updated_at:
                logging.debug('----------------------------------------')
                po.web_updated_at = result.updated_at
                po.web_status = result.status

                po.firstname = result.firstname
                po.lastname = result.lastname
                po.postcode = result.postcode
                po.phone = result.telephone

                # magneto地址是换行符分隔stree slik 2018-9-1
                str_street = result.street
                str_street = str_street.encode('utf-8')
                sec_str = '\n'
                arr_street = str_street.split(sec_str)

                po.street1 = arr_street[0]
                if len(arr_street) > 1:
                    po.street2 = arr_street[1]

                po.city = result.city
                po.region = result.region
                po.country_id = result.country_id

                po.is_verified_addr = True

                po.save()

                # return JsonResponse(queryset, safe=False)

        json_data = {}
        json_data['message'] = 'ok'
        json_data = json.dumps(json_data)
        return HttpResponse(json_data)
    except Exception as e:
        logging.exception(e.message)
        return HttpResponse(e.message)


@csrf_exempt
def redirect_qc_glasses_final_inspection(request):
    json_data = {}
    json_body = json.loads(request.body)
    try:
        json_obj = json_body.get('json_obj', '')
        logging.debug('json_obj: %s' % json_obj)

        if not json_obj == '':
            gfic = glasses_final_inspection_controller()
            res = gfic.add(request, json_obj)

            return HttpResponse(res)

        json_data['code'] = -1
        json_data['message'] = 'No Data'
        logging.debug('json_data: %s' % json_data)

        json_data['request_body'] = json_body

        json_data = json.dumps(json_data)
        return HttpResponse(json_data)
    except Exception as e:
        logging.exception(e.message)
        json_data['code'] = -8000
        json_data['message'] = e.message
        json_data['request_body'] = json_body

        json_data = json.dumps(json_data)

        return HttpResponse(json_data)


# 根据条码获得lab number
@csrf_exempt
def redirect_get_lab_number(request, params=''):
    try:
        order_number = params

        loc = lab_order_controller()
        lbos = loc.get_by_entity(order_number)

        if not lbos == None:

            lbo = lbos[0]

            lbo_dict = {}
            lbo_dict['lab_number'] = lbo.lab_number

            lbo_json = json.dumps(lbo_dict, cls=DateEncoder)

            return HttpResponse(lbo_json)
        else:
            return HttpResponse('Not found')
    except Exception as e:
        rvalue = '{"exception":"' + e.message + '"}'
        return HttpResponse(rvalue)


# 根据Order Number的集合 获得lab number的集合
@csrf_exempt
def redirect_get_lab_numbers(request):
    try:
        json_data = ''
        return HttpResponse(json_data)
    except Exception as e:
        logging.exception(e.message)
        return HttpResponse(e.message)


@login_required
@permission_required('oms.CHANGE_LAB_STATUS', login_url='/oms/forbid/')
def redirect_change_status(request):
    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Lens Registration'
    items = []
    lbo = None
    try:
        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')
            status_new = request.POST.get('status_new', '')
            status_reason = request.POST.get('status_reason', '')

            if lab_number == '':
                res['code'] = -1
                res['message'] = '请输入订单号!!'
                return HttpResponse(json.dumps(res))

            try:
                logging.debug('----------------------------------------')

                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_number)

                if len(lbos) == 1:
                    lbo = lbos[0]
                    lab_number = lbo.lab_number

                lbo = LabOrder.objects.get(lab_number=lab_number)

                msg = '原状态【%s】,新状态【%s】,原因【%s】'
                # 获取现在状态
                status_now = lbo.get_status_display()

                # 写入新状态
                lbo.status = status_new
                lbo.save()

                status_new = lbo.get_status_display()
                msg = msg % (status_now, status_new, status_reason)

                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, request.user, "CHANGE_STATUS", "状态调整", msg)

                _form_data['laborder'] = lbo

                res['code'] = 0
                res['message'] = 'ok'
                logging.debug('----------------------------------------')

            except Exception as e:
                res['code'] = -999
                res['message'] = '数据遇到异常: ' + str(e)

            return HttpResponse(json.dumps(res))

        # GET
        entity_id = request.GET.get('entity_id', '')
        # 生成可变状态列表
        status_list = []
        status_choice = LabOrder.STATUS_CHOICES
        for item in status_choice:
            value = {}
            value['key'] = item[0]
            value['value'] = item[1]
            status_list.append(value)
        _form_data['status_list'] = status_list
        lab_number = ''  # 类内使用
        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

        return render(request, "change_status.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('lens_registration'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e)
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('lens_registration'),
                      })


@csrf_exempt
def redirect_quality_inspection_query(request, params=''):
    res = {}
    res['code'] = 0
    res['body'] = ''
    res['message'] = ''
    try:
        order_number = params
        loc = lab_order_controller()
        lbos = loc.get_by_entity(order_number)
        if len(lbos) == 1:
            lbo = lbos[0]
            lab_number = lbo.lab_number

        lbo = LabOrder.objects.get(lab_number=lab_number)
        # 查询实际
        try:
            gli = glasses_final_inspection.objects.get(laborder_id=lbo.id)
        except Exception as e:
            res['code'] = -1
            res['message'] = "无终检数据"
            json_body = json.dumps(res, cls=DateEncoder)
            return HttpResponse(json_body)

        try:
            pa = prescripiton_actual.objects.get(pk=gli.prescripiton_actual_entity.id)
        except Exception as e:
            res['code'] = -1
            res['message'] = "无验光数据"
            json_body = json.dumps(res, cls=DateEncoder)
            return HttpResponse(json_body)

        try:
            gfit = glasses_final_inspection_technique.objects.get(laborder_id=lbo.id)
        except Exception as e:
            res['code'] = -1
            res['message'] = "无终检验光数据"
            json_body = json.dumps(res, cls=DateEncoder)
            return HttpResponse(json_body)

        lbo_dict = utilities.convert_to_dict(lbo)
        pa_dict = utilities.convert_to_dict(pa)
        gfit_dict = utilities.convert_to_dict(gfit)
        quality_dict = {}

        quality_dict['lab_order'] = lbo_dict
        quality_dict['prescripiton_actual'] = pa_dict
        quality_dict['gfit'] = gfit_dict

        res['body'] = quality_dict
        res['message'] = '获取成功'
        quality_json = json.dumps(res, cls=DateEncoder)

        return HttpResponse(quality_json)

    except Exception as e:
        rvalue = '{"exception":"' + e.message + '"}'
        res['code'] = -1
        res['message'] = rvalue
        json_body = json.dumps(res, cls=DateEncoder)
        return HttpResponse(json_body)


# 设置pgorderitem,状态标识为有图
@csrf_exempt
def set_is_has_imgs(request):
    res = {}
    try:
        logging.debug('request=%s' % request)
        received_json_data = json.loads(request.body)
        order_id = received_json_data['order_entity']
        order_id = int(order_id)
        item_id = received_json_data['order_item_entity']
        item_id = int(item_id)
        logging.debug('item_id=%s' % item_id)
        if item_id > 0:
            pgois = PgOrderItem.objects.filter(item_id=item_id)
            if (pgois.count() == 0):
                res['code'] = -1
                res['message'] = '未找到对应订单'
                quality_json = json.dumps(res, cls=DateEncoder)
                return HttpResponse(quality_json)
            pgoi = pgois[0]
            pgoi.is_has_imgs = True
            pgoi.save()
            res['code'] = 0
            res['message'] = '状态写入成功'
            quality_json = json.dumps(res, cls=DateEncoder)
            return HttpResponse(quality_json)
        elif order_id > 0:
            pgos = PgOrder.objects.filter(base_entity=order_id)
            if (pgos.count() == 0):
                res['code'] = -1
                res['message'] = '未找到对应PgOrder'
                quality_json = json.dumps(res, cls=DateEncoder)
                return HttpResponse(quality_json)
            pgo = pgos[0]
            pg_order_id = pgo.order_number
            pgis = PgOrderItem.objects.filter(order_number=pg_order_id)
            for i in pgis:
                i.is_has_imgs = True
                i.save()
            res['code'] = 0
            res['message'] = '状态写入成功'
            quality_json = json.dumps(res, cls=DateEncoder)
            return HttpResponse(quality_json)
        else:
            res['code'] = -1
            res['message'] = '未给出匹配数据'
            quality_json = json.dumps(res, cls=DateEncoder)
            return HttpResponse(quality_json)
    except Exception as e:
        print(e)
        print(1111111111)
        res['code'] = -1
        res['message'] = str(e)
        quality_json = json.dumps(res, cls=DateEncoder)
        return HttpResponse(quality_json)


# PgOrderItem 有图标志
class PgOrderItemIsHasImgs(APIView):
    def getIsHasImgs(self, request):
        # 通过item_id，或者order_number匹配
        item_id = request.GET.get('item_id', '')
        order_number = request.GET.get('order_number', '')
        logging.debug('调用查询方法')
        try:
            if item_id:
                pgi_is_has_imgs = PgOrderItem.objects.filter(item_id=item_id)[0]
            else:
                pgi_is_has_imgs = PgOrderItem.objects.get(order_number=order_number)
            return pgi_is_has_imgs
        except pgi_is_has_imgs.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        logging.debug('GET方法')
        pgi_is_has_imgs = self.getIsHasImgs(request)
        serializer = PgOrderItem_IsHasImgsSerializers(pgi_is_has_imgs)
        return Response(serializer.data)


# laborder video数据接口,lab_order的video
class LaborderAccessories(APIView):
    def get(self, request, format=None):
        lab_number = request.GET.get('lab_number', '')
        accessories_type = request.GET.get('accessories_type', '')
        if lab_number == '':
            return JsonResponse(data=request.data, code=400, msg="lab_number is none",
                                status=status.HTTP_400_BAD_REQUEST)
        if accessories_type == '':
            return JsonResponse(data=request.data, code=400, msg="accessories_type is none",
                                status=status.HTTP_400_BAD_REQUEST)
        items = laborder_accessories.objects.filter(lab_number=lab_number, accessories_type=accessories_type)
        serializer = LaborderAccessoriesSerializers(items, many=True)
        return JsonResponse(data=serializer.data, code=200, msg="Success", status=status.HTTP_200_OK)

    def post(self, request, format=None):
        lab_as = LaborderAccessoriesSerializers(data=request.data)
        if lab_as.is_valid():
            lab_as.save()
            return JsonResponse(data=lab_as.data, code=200, msg="Success", status=status.HTTP_200_OK)
        return JsonResponse(data=lab_as.data, code=400, msg="ERROR", status=status.HTTP_400_BAD_REQUEST)


# 入库记录(调用它创建入库记录时完成入库）
class InventoryReceiptLens(APIView):
    def post(self, request, format=None):
        item = json.loads(request.body)
        # Xwrztzp6m8ZXRbfE
        key = item['key']

        if not key == 'Xwrztzp6m8ZXRbfE':
            return JsonResponse(data='', code=400, msg='口令错误', status=status.HTTP_400_BAD_REQUEST)

        doc_number = time.strftime('%Y%m%d', time.localtime(time.time()))
        doc_type = item['doc_type']
        warehouse_code = item['warehouse_code']
        sku = item['sku']
        quantity = item['quantity']
        sph = item['sph']
        cyl = item['cyl']
        add = item['add']
        try:
            islc = inventory_receipt_lens_controller()
            rm = islc.add('', doc_number, doc_type, warehouse_code, sku, quantity, sph, cyl, add, 0, '',
                          '', '', '调用接口入库', '')
            if rm.code == 0:
                return JsonResponse(data='', code=200, msg="Success", status=status.HTTP_200_OK)
            else:
                return JsonResponse(data='', code=400, msg=rm.message, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=str(e), status=status.HTTP_400_BAD_REQUEST)


# 镜片库存结构
class LensInventoryStructs(APIView):
    def get(self, request, format=None):
        wh_code = request.GET.get('wh_code', '')
        sku = request.GET.get('sku', '')
        lab_sku = request.GET.get('lab_sku', '')
        web_sku = request.GET.get('web_sku', '')
        sph = request.GET.get('sph', '')
        cyl = request.GET.get('cyl', '')
        # sql 语句
        sql = ''
        _items = []
        if wh_code == '':
            return JsonResponse(data=request.data, code=400, msg="请给出仓库代码(wh_code)", status=status.HTTP_400_BAD_REQUEST)
        if sku == '' and lab_sku == '' and web_sku == '':
            return JsonResponse(data=request.data, code=400, msg="仓库_sku(sku),工厂_SKU(lab_sku)，WEB_SKU(web_sku)至少给出一个",
                                status=status.HTTP_400_BAD_REQUEST)
        if not sku == '':
            if not sph == '' and not cyl == '':
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and sku='%s' and sph='%s' and cyl='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, sku, sph, cyl)
            else:
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and sku='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, sku)
        if not lab_sku == '':
            if not sph == '' and not cyl == '':
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and base_sku='%s'and sph='%s' and cyl='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, lab_sku, sph, cyl)
            else:
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and base_sku='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, lab_sku)
        if not web_sku == '':
            # oms_pgproduct 存放网站SKU，其中的lab_product_id唯一对应oms_labproduct表 。lab_product的SKU就是BASE_SKU
            pgp = PgProduct.objects.filter(sku=web_sku).values('lab_product_id')
            if pgp.count() == 0:
                return JsonResponse(data=request.data, code=400, msg='未找到web_sku', status=status.HTTP_400_BAD_REQUEST)
            labp = LabProduct.objects.filter(id=pgp[0]['lab_product_id']).values('sku')
            if labp.count() == 0:
                return JsonResponse(data=request.data, code=400, msg='未找到web_sku对应的lab_sku',
                                    status=status.HTTP_400_BAD_REQUEST)

            if not sph == '' and not cyl == '':
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and base_sku='%s'and sph='%s' and cyl='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, labp[0]['sku'], sph, cyl)
            else:
                sql = '''
                        SELECT name,sku,base_sku,sph,cyl,sum(quantity) quantity
                        FROM wms_inventory_struct_lens_batch 
                        where warehouse_code = '%s' and base_sku='%s'
                        GROUP BY sph,cyl
                    ''' % (wh_code, labp[0]['sku'])
        try:
            with connections["pg_oms_query"].cursor() as cursor:
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
                for r in results:
                    rest = {}
                    rest['name'] = r.name
                    rest['sku'] = r.sku
                    rest['base_sku'] = r.base_sku
                    rest['sph'] = r.sph
                    rest['cyl'] = r.cyl
                    rest['quantity'] = r.quantity
                    _items.append(rest)
            return JsonResponse(data=_items, code=200, msg="Success", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data=request.data, code=400, msg=str(e), status=status.HTTP_400_BAD_REQUEST)


# 镜架库存结构表状态
class InventoryStructsStatus(APIView):
    def post(self, request, format=None):
        rq_js = request.data
        # 取请求参数
        try:
            sku = rq_js['sku']
            # 验证SKU是否正确
            iss = inventory_struct.objects.filter(sku=sku)
            if iss.count() < 1:
                return JsonResponse(data='sku不存在', code=400, msg="Error", status=status.HTTP_400_BAD_REQUEST)
            new_status = rq_js['status']
            if new_status not in ('OUT_OF_STOCK', 'IN_STOCK', 'DRAFT'):
                return JsonResponse(data='设置状态出错', code=400, msg="Error", status=status.HTTP_400_BAD_REQUEST)
            reason = rq_js['reason']
            user_id = rq_js['user_id']
            user_name = rq_js['user_name']
            # 更新状态
            is_obj = iss[0]
            is_obj.status = new_status
            is_obj.save()
        except Exception as e:
            return JsonResponse(data=str(e), code=400, msg="Error", status=status.HTTP_400_BAD_REQUEST)
        # 记录日志
        ol = inventory_operation_log()
        ol.api_log(sku, reason, new_status, user_id, user_name)
        return JsonResponse(data='', code=200, msg="Success", status=status.HTTP_200_OK)


# 保险
class PgOrder_Invoice(APIView):
    def post(self, request, format=None):
        rq_js = request.data
        # 取请求参数
        try:
            order_number = rq_js.get("order_number", "")
            invoice_id = rq_js.get("invoice_id", "")

            if order_number == '' or invoice_id == '':
                return JsonResponse(data='', code=400, msg='参数错误', status=status.HTTP_400_BAD_REQUEST)

            pg_order_invs = PgOrderInvoice.objects.filter(order_number=order_number, invoice_id=invoice_id)

            if len(pg_order_invs) > 0:
                pg_order_inv = pg_order_invs[0]
                pg_order_inv.status = "PAID"
                pg_order_inv.save()
            else:
                return JsonResponse(data='', code=400, msg='PgOrderInvoice 未找到', status=status.HTTP_400_BAD_REQUEST)

            subject = "Ticket NO: {0}".format(pg_order_inv.ticket_no)
            message = "Ticket No: {0} Order Number:{1}   Comments: The invoice has been paid......".format(
                pg_order_inv.ticket_no, order_number)
            rm = SendEmail().send_email('help@payneglasses.com', subject, message)
            if rm.code != 0:
                return JsonResponse(data='', code=400, msg=rm.message, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse(data='', code=200, msg="Success", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data=str(e), code=400, msg=e, status=status.HTTP_400_BAD_REQUEST)


class GetPgOrders(APIView):
    def get(self, request, format=None):
        try:
            items = []
            order_number = format
            logging.debug(format)
            if format == '' or format is None:
                return JsonResponse(data='', code=400, msg='订单号为空！', status=status.HTTP_400_BAD_REQUEST)
            pgo = PgOrder.objects.get(order_number=order_number)
            pgorder_items = PgOrderItem.objects.filter(order_number=order_number)
            pgo_dict = model_to_dict(pgo)
            for item in pgorder_items:
                items.append(model_to_dict(item))
            data = {'pgo': pgo_dict, 'items': items}
            return JsonResponse(data=data, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=str(e), status=status.HTTP_400_BAD_REQUEST)


# shipment操作历史表
class ShipmentHistorys(APIView):
    def post(self, request, format=None):
        # 请求参数
        response_dict = {}
        error_list = []
        success_list = []
        js_error_list = None
        js_success_list = None
        request_data = request.data
        try:
            for item in request_data:
                # 序列化
                sh = ShipmentHistorySerializers(data=item)
                # 对象化
                if sh.is_valid():  # 对象化成功
                    sh.save()
                    success_list.append(item['shipping_id'])
                    js_success_list = json.dumps(success_list)
                else:
                    error_list.append(item['shipping_id'])
                    js_error_list = json.dumps(error_list)

            return JsonResponse(data={'error_list': js_error_list, 'success_list': js_success_list}, code=200,
                                msg="Success", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='Exception:' + str(e), code=400, msg='异常报错', status=status.HTTP_400_BAD_REQUEST)

# SHIP收到easypostwebhooks后更新lab_order的状态
class SetLabOrderStatusDelivered(APIView):
    def put(self, request):
        try:
            logging.debug('更新已发货')
            # 获取请求数据
            request_data = request.data
            lab_number = request_data['lab_number']
            lab_status = request_data['status']
            status_detail = request_data['status_detail']
            tracking_code = request_data.get('tracking_code','')
            logging.debug(lab_number)
            # 是妥投状态
            if lab_status == 'delivered':
                # 查询lab对象
                lbo_entitys = LabOrder.objects.filter(lab_number=lab_number)
                if lbo_entitys.count() < 1:
                    return JsonResponse(data=lab_number, code=400, msg='订单不存在', status=status.HTTP_400_BAD_REQUEST)
                lbo_entity = lbo_entitys[0]
                if lbo_entity.status == 'DELIVERED':
                    return JsonResponse(data=lab_status, code=400, msg='已是妥投状态,不更新', status=status.HTTP_400_BAD_REQUEST)
                # 设置更新字典
                update_dict = {}
                update_dict['status'] = 'DELIVERED'  # 妥投
                update_dict['delivered_at'] = datetime.datetime.now()
                update_dict['tracking_code'] = tracking_code
                # 序列化
                up_enty = LabOrderSerializers(instance=lbo_entity, data=update_dict)
                # 更新
                if up_enty.is_valid():
                    up_enty.save()
                    # 写TRACKING
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo_entity, None, 'DELIVERED', '妥投', status_detail)

                    order_number = lbo_entity.order_number
                    poc = pg_order_controller()
                    s2delivered = poc.set_order2delivered(request, order_number)

                    logging.debug('写记录' + str(lbo_entity.lab_number))
                    return JsonResponse(data=up_enty.data, code=200, msg='Success', status=status.HTTP_200_OK)
                return JsonResponse(data=up_enty.errors, code=400, msg='Error', status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse(data=lab_status, code=400, msg='不更新', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse(data=str(e), code=400, msg='Exception', status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def RedirectDingdingChat(request):
    res = {}
    ddc = DingdingChat()
    message = request.POST.get("message")
    chat_id = request.POST.get("chat_id")
    mobile = request.POST.get("mobile")
    agent_id = request.POST.get("agent_id")
    try:
        # 2019.10.14 by guof.
        # 调整为支持body的参数方式
        body = request.body
        body = json.loads(body)
        chat_id = body.get('chat_id', '')
        message = body.get('message', '')
        mobile = body.get('mobile', '')
        agent_id = body.get('agent_id', '')
        logging.debug('--------------------------------------------------------------------------------')
        logging.debug(chat_id)

        if chat_id == '' or chat_id == None:
            res['code'] = -1
            res['message'] = "chat_id can't be null."
            from django.http import HttpResponse, JsonResponse
            return JsonResponse(res)
        if message == '' or message == None:
            res['code'] = -1
            res['message'] = "message content cont't be null."
            from django.http import HttpResponse, JsonResponse
            return JsonResponse(res)

        try:
            if agent_id == '' or agent_id == None:
                rm = ddc.send_text_to_chat(chat_id, message, mobile)
            else:
                rm = ddc.send_message_plain_text(agent_id, message)
                # send_text_to_chat(access_token,'chat5f559dbc56321c9a4782dcf7a7bd06b3',"这是一条测试")
            logging.debug(rm.code)
            res['code'] = rm.code
            res['message'] = rm.message
            from django.http import HttpResponse, JsonResponse
            return JsonResponse(res)

        except Exception as e:
            logging.debug(e)
            res['code'] = -1
            res['message'] = str(e)
            from django.http import HttpResponse, JsonResponse
            return JsonResponse(res)
    except Exception as ex:
        res['code'] = -1
        res['message'] = str(ex)
        from django.http import HttpResponse, JsonResponse
        return JsonResponse(res)


class GetDeliveryInfo(APIView):
    def get(self, request, format=None):
        data_list = {}
        try:
            sql = """SELECT sku, COUNT(1) as cnt FROM wms_inventory_delivery WHERE doc_type='AUTO' GROUP BY sku"""
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                delivery_list = dictfetchall(cursor)
                for item in delivery_list:
                    data_list[item['sku']] = item
            return JsonResponse(data=data_list, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=str(e), status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def pg_order_hold_request(request):
    rm =response_message()
    entity_id = request.POST.get("entity_id")
    item_id = request.POST.get("item_id")
    reason = request.POST.get("reason")
    order_number = request.POST.get("order_number")
    ticket_number = request.POST.get("ticket_number")
    is_web = request.POST.get("is_web", 'Y')
    res = {}
    logging.debug(entity_id)
    try:
        pgc = pg_order_controller(order_number)
        rm = pgc.hold(request, entity_id, item_id, reason, ticket_number, is_web)
        logging.debug(rm.code)
        res['code'] =rm.code
        res['message'] = rm.message
        from django.http import HttpResponse, JsonResponse
        return JsonResponse(res)

    except Exception as e:
        logging.debug(e)
        res['code'] = -1
        res['message'] = e.message
        from django.http import HttpResponse, JsonResponse
        return JsonResponse(res)


class GetOrderDeliveredList(APIView):
    def get(self, request, format=None):
        data_list = []
        try:
            sql = """
              SELECT id, order_number,lab_number,order_datetime,delivered_at
              FROM oms_laborder WHERE `status`='DELIVERED'
              """

            order_number = request.query_params.dict().get('order_number', '')
            ship_direction = request.query_params.dict().get('ship_direction', '')
            order_status = request.query_params.dict().get('status', '')

            if order_number== '' and ship_direction == '' and order_status == '':
                start_date = request.query_params.dict().get('start_date', '')
                end_date = request.query_params.dict().get('end_date', '')
                update_start_date = request.query_params.dict().get('update_start_date', '')
                update_end_date = request.query_params.dict().get('update_end_date', '')

                if start_date == '' and end_date == '' and update_start_date == '' and update_end_date == '':
                    return JsonResponse(data='', code=400, msg='开始时间或结束时间与其他条件不能同时为空'
                                        , status=status.HTTP_400_BAD_REQUEST)

                now_date = datetime.date.today()

                if start_date == '' and end_date == '':
                    if update_start_date == '':
                        update_start_date = '2019-01-01'

                    if update_end_date == '':
                        update_end_date = now_date

                    if update_start_date == update_end_date:
                        sql = sql + """ AND date(update_at)='%s' """ % update_start_date
                    else:
                        sql = sql + """ AND (date(update_at)='%s' OR update_at BETWEEN '%s' AND '%s') """ % (update_end_date, update_start_date, update_end_date)
                else:
                    if start_date == '':
                        start_date = '2019-01-01'

                    if end_date == '':
                        end_date = now_date

                    if update_start_date == '' and update_end_date == '':
                        if start_date == end_date:
                            sql = sql + """ AND date(delivered_at)='%s' """% start_date
                        else:
                            sql = sql + """ AND (date(delivered_at)='%s' OR delivered_at BETWEEN '%s' AND '%s') """ %(end_date, start_date, end_date)
                    else:
                        if update_start_date == '':
                            update_start_date = '2019-01-01'

                        if update_end_date == '':
                            update_end_date = now_date

                        if start_date == end_date:
                            if update_start_date == update_end_date:
                                sql = sql + """ AND (date(delivered_at)='%s' OR date(update_at)='%s') """% (start_date, update_start_date)
                            else:
                                sql = sql + """ AND (date(delivered_at)='%s' OR (date(update_at)='%s' OR update_at BETWEEN '%s' AND '%s')) """% (start_date, update_end_date, update_start_date, update_end_date)
                        else:
                            if update_start_date == update_end_date:
                                sql = sql + """ AND ((date(delivered_at)='%s' OR delivered_at BETWEEN '%s' AND '%s') OR date(update_at)='%s') """ % (
                                end_date, start_date, end_date, update_start_date)
                            else:
                                sql = sql + """ AND ((date(delivered_at)='%s' OR delivered_at BETWEEN '%s' AND '%s') OR (date(update_at)='%s' OR update_at BETWEEN '%s' AND '%s')) """ %(end_date, start_date, end_date, update_end_date, update_start_date, update_end_date)
                        sql = sql + ' ORDER BY delivered_at'

            else:
                ext_conditions = ""
                if order_number !='':
                    ext_conditions = """
                    and order_number='%s'
                    """ % order_number
                if ship_direction != '':
                    ext_conditions += """
                    and ship_direction='%s'
                    """ % ship_direction
                if order_status != '':
                    ext_conditions += """
                    and status='%s'
                    """ % order_status
                ext_conditions += ' ORDER BY delivered_at limit 10000'
                sql += ext_conditions

            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                lab_orders = namedtuplefetchall(cursor)
                for item in lab_orders:
                    data_list.append({
                        'id':item.id,
                        'order_number': item.order_number,
                        'order_datetime': item.order_datetime,
                        'lab_number': item.lab_number,
                        'delivered_at': item.delivered_at
                    })
            return JsonResponse(data=data_list, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=str(e), status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def pg_cancle_warranty_request(request):
    resp = 'error'
    res = {}
    username=request.user.username
    from django.http import HttpResponse, JsonResponse
    if request.method == 'POST':

        entity_id = request.POST.get("entity_id")
        reason = request.POST.get("reason")
        order_number = request.POST.get("order_number")

        req_url = settings.CANCELWARRENTY_BASE_URL + settings.CANCELWARRENTY_ADDRESS
        # req_url = "https://beta3.payneglasses.com:444/prescription/open/cancelWarrenty?order_id="+entity_id
        req_url = req_url+"?order_id="+entity_id
        logging.debug("req_url==>%s" % req_url)

        http_headers = {
            'Content-Type': 'application/json'
        }

        logging.debug("http_headers==>%s" % http_headers)

        try:
            # req = urllib2.Request(url=req_url, data=send_data, headers=http_headers)
            # res = urllib2.urlopen(req)
            req = requests.post(url=req_url, headers=http_headers,timeout=60, verify=False)
            resp = req.text
            # resp = res.read()
            logging.debug(resp)
            res_json = json.loads(resp)
            status = res_json.get('status', '')
            errMsg = res_json.get('errMsg', '')
            if status == False:
                res['code'] = -1
                res['message'] = errMsg
                return JsonResponse(res)
            elif status == True:
                # `has_warranty`, `warranty` 置为0
                pgo = PgOrder.objects.get(order_number=order_number)
                pgo.warranty = 0
                pgo.has_warranty = False
                pgo.save()

                pg_order_id = pgo.order_number
                pgis = PgOrderItem.objects.filter(order_number=pg_order_id)
                for i in pgis:
                    i.warranty = 0
                    i.has_warranty = False
                    i.save()

                dt = datetime.datetime.utcnow()+datetime.timedelta(hours=+8)
                create_at=dt.strftime("%Y-%m-%d %H:%M:%S")
                # 撤销后保留日志：撤销时间，撤销备注，撤销金额，操作人
                pg_order_inv = PgOrderInvoice()
                pg_order_inv.pg_order_entity_id = entity_id
                pg_order_inv.order_number = order_number
                pg_order_inv.inv_type = 'warranty'
                pg_order_inv.comments = username+" "+create_at+" :"+reason
                pg_order_inv.save()

                res['code'] = 0
                res['message'] = "cancle warranty success!"
                return JsonResponse(res)

            return JsonResponse(res)
        except Exception as e:
            logging.debug(e)
            res['code'] = -1
            res['message'] = e.message
        return JsonResponse(res)

def getToken():
    # logging.debug("-------------------gettoken---------------------")
    get_token_url = settings.BASE_URL  + oms.const.token_url
    api_response = requests.post(get_token_url, data=json.dumps(oms.const.token_data), headers=oms.const.token_header,timeout=60, verify=False)
    # logging.debug("-------------------token:%s---------------------"%api_response.text.replace('"', ''))
    return api_response.text.replace('"', '')

#根据产品获取sku
def getPrdBysku(sku):
    get_token_url = settings.BASE_URL  + "V1/products/"+sku
    http_headers = {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
    }
    api_response = requests.get(get_token_url, headers=http_headers,timeout=60, verify=False)
    return api_response.text

#对比时间大小
def compare_time(time1, time2):
    d1 = datetime.datetime.strptime(time1, '%Y-%m-%d %H:%M:%S')
    d2 = datetime.datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
    delta = d1 - d2
    if delta.days >= 0:
        return True
    else:
        return False


#获取特殊价格
#设置为原价，如果有special_price会替换为特殊价格，返回时直接对比即可，在外面对比
def get_prd_final_price(prd_info):
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    special_price = ''
    special_from_date = ''
    special_to_date = ''
    final_price = prd_info.get('price')
    price = prd_info.get('price')
    try:
        # 判断special price价格
        if prd_info.has_key('custom_attributes'):
            special_price_list = [val for val in prd_info['custom_attributes'] if val['attribute_code'] == "special_price"]
            special_from_date_list = [val for val in prd_info['custom_attributes'] if
                                      val['attribute_code'] == "special_from_date"]
            special_to_date_list = [val for val in prd_info['custom_attributes'] if
                                    val['attribute_code'] == "special_to_date"]
            if (len(special_price_list)):
                special_price = special_price_list[0]['value']
            if (len(special_from_date_list)):
                special_from_date = special_from_date_list[0]['value']
            if (len(special_to_date_list)):
                special_to_date = special_to_date_list[0]['value']

            # 查询特殊价格
            if (len(special_price_list)):
                # 如果没有设置日期，设置了特殊价格，并且小于price
                if (len(special_from_date_list) == 0 and len(special_to_date_list) == 0):
                    final_price = special_price

                # 如果设置了起始日期，没设置终止日期，设置了特殊价格，并且小于price
                if (len(special_from_date_list) > 0 and len(special_to_date_list) == 0):
                    if (compare_time(time_now, special_from_date) ):
                        final_price = special_price

                # 如果设置了终止日期，没设置起始日期，设置了特殊价格，并且小于price
                if (len(special_from_date_list) == 0 and len(special_to_date_list) > 0):
                    if (compare_time(special_to_date, time_now) and special_price < price):
                        final_price = special_price

                # 如果设置了起始日期和终止日期，设置了特殊价格，并且小于price
                if (len(special_from_date_list) > 0 and len(special_to_date_list) > 0):
                    if (compare_time(time_now, special_from_date) and compare_time(special_from_date,time_now)):
                        final_price = special_price
    except Exception as e:
        logging.debug("价格获取错误")
    return final_price

#对比价格,返回最小值
def compare_price(d1,d2):
    if float(d1) - float(d2) >= 0:
        return d2
    else:
        return d1

# 获取镜架属性对象
def get_color_list(value):
    url = settings.BASE_URL + 'V1/products/attributes?searchCriteria[filter_groups][0][filters][0][field]=attribute_code&searchCriteria[filter_groups][0][filters][0][value]=%s&searchCriteria[filter_groups][0][filters][0][condition_type]=eq' % value
    http_headers = {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
    }
    api_response = requests.get(url, headers=http_headers, timeout=10, verify=False)
    return api_response.text

# 插入明细
def append_glasses_item(dict_order,pocs,order_number,freight_amount=0):
    weight = 0
    price = 0
    row_total = 0
    discount_amount = 0
    qty_ordered = 0
    arr_items = []
    for poc in pocs:
        item = json.loads(poc.item_options,object_pairs_hook=OrderedDict)
        weight += item['0']['weight']
        price += item['0']['price']
        row_total += item['0']['row_total']
        discount_amount += item['0']['discount_amount']
        qty_ordered += item['0']['qty_ordered']
        arr_items.append(item)
    #
    # dict_order['items'][0] = ""
    # dict_order['items'][1] = frame_info

    # 折扣价格，为负数："base_discount_amount","base_discount_invoiced","discount_amount","discount_invoiced"
    discount_price = 0 - price
    dict_order['base_discount_amount'] = discount_price
    dict_order['base_discount_invoiced'] = discount_price
    dict_order['discount_amount'] = discount_price
    dict_order['discount_invoiced'] = discount_price

    # 为订单赋值
    dict_order['total_qty_ordered'] = qty_ordered
    dict_order['base_total_qty_ordered'] = qty_ordered

    sum_total = price  + freight_amount
    dict_order['base_subtotal'] = freight_amount

    dict_order['base_total_invoiced_cost'] = freight_amount
    dict_order['base_total_qty_ordered'] = 1
    dict_order['base_total_paid'] = freight_amount
    dict_order['grand_total'] = freight_amount

    dict_order['total_invoiced'] = freight_amount
    dict_order['total_paid'] = freight_amount
    # 退款和取消金额
    dict_order['base_subtotal_canceled'] = 0.00
    dict_order['base_subtotal_refunded'] = 0.00

    dict_order['subtotal'] = sum_total
    dict_order['subtotal_invoiced'] = sum_total
    dict_order['base_subtotal_incl_tax'] = sum_total
    dict_order['subtotal_incl_tax'] = sum_total

    dict_order['weight'] = weight
    dict_order['total_item_count'] = qty_ordered
    items = dict_order['items']
    #configuable item
    dict_order['items'] = arr_items

    return dict_order

#对比验光单主要数据
def compare_rx(new_rx,origin_rx):
    rx_int_list = ['rsph', 'lsph', 'rcyl', 'lcyl', 'rax', 'radd', 'ladd', 'pd', 'rpd', 'lpd', 'rpri', 'lpri', 'rpri_1','lpri_1']
    rx_str_list = ['rbase', 'lbase', 'rbase_1', 'lbase_1']
    for v in rx_int_list:
        if not new_rx[v]:
            new_rx[v] = 0
        if not origin_rx[v]:
            origin_rx[v] = 0
        if float(new_rx[v]) != float(origin_rx[v]):
            return  False

    for v in rx_str_list:
        if not new_rx[v]:
            new_rx[v] = ''
        if not origin_rx[v]:
            origin_rx[v] = ''
        if new_rx[v] != origin_rx[v]:
            return  False
    return True


#判断是否修改了验光单
def is_rx_updated(poi,dict_info):
    sql = '''select entity_id,prescription_name,rsph,lsph,rcyl,lcyl,rax,lax,rpri,lpri,rpri_1,lpri_1,
                    IFNULL(rbase,'') rbase,IFNULL(lbase,'') lbase,IFNULL(rbase_1,'') rbase_1,IFNULL(lbase_1,'') lbase_1,single_pd,
                    radd,ladd,pd,rpd,lpd,exam_date,parent_id,expire_date
                    from prescription_entity where entity_id=%s''' % poi.profile_prescription_id
    obj = dict_info['profile_prescription']
    print("============obj=============")
    print(json.dumps(obj))
    print("============obj=============")
    with connections['pg_mg_query'].cursor() as cursor:
        cursor.execute(sql)
        results = dictfetchall(cursor)
        if(len(results)>0):
            origin_rx = json.loads(json.dumps(results[0],cls=DateEncoder))
            if(compare_rx(obj,origin_rx)):
                origin_rx['is_update'] = 0
                origin_rx['exam_date'] = '01/01/1970'
                origin_rx['expire_date'] = '01/01/1970'
                return {"status":0,"msg":"this rx not update","rx":origin_rx}
            else:
                #如果修改重新赋值
                if(obj.has_key('progressive_code')):
                    obj.pop("progressive_code")
                if (obj.has_key('exam_date') and origin_rx['exam_date']):
                    obj["exam_date"] = origin_rx['exam_date']
                else:
                    obj["exam_date"] = '01/01/1970'
                obj["profile_id"] = origin_rx['parent_id']
                obj["prescription_name"] = origin_rx['prescription_name']
                if(origin_rx['expire_date']):
                   obj["expire_date"] = origin_rx['expire_date']
                else:
                   obj["expire_date"] = '01/01/1970'
                   obj["exam_date"] = '01/01/1970'
                obj['is_update'] = 1 #修改了验光单

                #需要修改的验光单ID
                obj["entity_id"] =poi.profile_prescription_id
                return {"status": 1, "msg": "rx is updated!","rx":obj}
        else:
                return {"status": -1, "msg": "","rx":""}

#检查网站库存
def check_web_inventory(sku):
    stock_url = settings.PG_INVENTORY_HOST +"inventory/api/"
    getPrdBysku(sku)
    # ck_sku_list()


def get_order_info(order_number):
    order_info_url= settings.BASE_URL+'V1/orders?searchCriteria[filter_groups][2][filters][0][field]=increment_id&searchCriteria[filter_groups][2][filters][0][value]=%s&searchCriteria[filter_groups][2][filters][0][condition_type]=eq&fields=items[payment]'

    http_headers = {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
    }
    api_response = requests.get(order_info_url % order_number, headers=http_headers, timeout=30, verify=False)
    return api_response.text

#生成订单
def gennerate_web_order(request):
    f = open("reorder.txt", 'a')
    dic_order_info = json.loads(request.body)
    f.write("\n========1.请求信息=================\n")
    f.write(dic_order_info['order_number'])
    f.write("\n========请求信息=================\n")

    # order_number = dic_order_info['order_number']
    order_number = dic_order_info['order_number']
    po = PgOrder.objects.get(order_number=order_number)
    # poi = PgOrderItem.objects.get(order_number=order_number)

    shipping_info = dic_order_info.get('shipping_method', '')
    list_shipping_method = DICT_SHIPPING_METHODS[po.country_id]
    k = [val for val in list_shipping_method if val['id'] == shipping_info]
    if (len(k) > 0):
        shipping_description = k[0]['description']
        shipping_method = k[0]['id']
    else:
        shipping_description = po.shipping_description
        shipping_method = po.shipping_method

    payment_method = ''
    try:
        PaymentInfo = get_order_info(po.order_number)
        payinfo = json.loads(PaymentInfo)
        payment_method = payinfo['items'][0]['payment']['method']
    except Exception as e:
        payment_method = 'stripecreditcards'
        f.write("\n========获取支付信息失败================\n")
        f.write(str(e))

    street1 = po.street
    if (not street1):
        street1 = ''

    street2 = po.street2
    if (not street2):
        street2 = ''

    freight_amount = 0.00
    dic_order = {
        "status": "processing",
        "state": "processing",
        "applied_rule_ids": "",
        "base_currency_code": "USD",

        "base_discount_amount": 0,
        "base_discount_invoiced": 0,
        "discount_amount": 0,
        "discount_invoiced": 0,

        "base_grand_total": 0,
        "base_discount_tax_compensation_amount": 0,
        "base_shipping_amount": freight_amount,
        "base_shipping_discount_amount": 0,
        "base_shipping_tax_amount": freight_amount,
        "shipping_tax_amount": freight_amount,
        "base_total_online_refunded": 0.00,
        "base_total_refunded": 0.00,
        "total_refunded": 0.00,
        "total_offline_refunded": 0.00,
        "shipping_incl_tax": freight_amount,
        "base_shipping_incl_tax": freight_amount,
        "shipping_amount": freight_amount,
        "total_due": freight_amount,
        # ------------需重新赋值----------------
        "base_subtotal": 0.00,
        "base_total_invoiced_cost": 0.00,
        "base_total_qty_ordered": 1,
        "base_total_paid": 0.00,
        "grand_total": 0.00,
        "total_invoiced": 0.00,
        "total_paid": 0.00,
        # 不包含运费
        "base_subtotal_canceled": 0.00,
        "base_subtotal_refunded": 0.00,
        "subtotal": 0.00,
        "subtotal_invoiced": 0.00,
        "base_subtotal_incl_tax": 0.00,
        "subtotal_incl_tax": 0.00,

        "total_item_count": 0,
        # ------------赋值结束----------------

        "base_tax_amount": 0,
        "base_total_due": 0,
        "base_to_global_rate": 1,
        "base_to_order_rate": 1,
        "customer_email": po.email,
        "customer_firstname": po.firstname,
        "customer_group_id": 1,
        "customer_id": po.customer_id,
        "customer_is_guest": 0,
        "customer_lastname": po.lastname,
        "customer_note_notify": 1,

        "discount_description": "",
        "global_currency_code": "USD",
        "discount_tax_compensation_amount": 0,
        "is_virtual": 0,
        "order_currency_code": "USD",
        "remote_ip":"oms.payneglasses.com",

        "shipping_description": shipping_description,
        "shipping_discount_amount": 0,
        "shipping_discount_tax_compensation_amount": 0,

        "store_currency_code": "USD",
        "store_id": 1,
        "store_to_base_rate": 0,
        "store_to_order_rate": 0,
        "tax_amount": 0,

        "total_qty_ordered": 1,
        "weight": 0,
        "items": {
        },
        "status_histories": [],
        "addresses": {
            "0": {
                "customer_address_id": po.shipping_address_id,
                "firstname": po.firstname,
                "lastname": po.lastname,
                "street": street1 + street2,
                "city": po.city,
                "region": po.region,
                "region_id": po.region,
                "postcode": po.postcode,
                "country_id": po.country_id,
                "telephone": po.phone,
                "email": po.email,
                "address_type": "shipping"
            },
            "1": {
                "customer_address_id": po.shipping_address_id,
                "firstname": po.firstname,
                "lastname": po.lastname,
                "street": street1 + street2,
                "city": po.city,
                "region": po.region,
                "region_id": po.region,
                "postcode": po.postcode,
                "country_id": po.country_id,
                "telephone": po.phone,
                "email": po.email,
                "address_type": "billing"
            }
        },
        "shipping_method": shipping_method,
        "payment": {
            "method": payment_method
        },
        "mailchimp_abandonedcart_flag": "0",
        "mailchimp_flag": 0,

        "is_php": 0,
        "is_clone": 1,
        "clone_options":
            {"params": {
                "order_id": po.id,
                "order_number": po.order_number,
                "is_redo": 1
            }
            },
        "clone_order_id": po.id,
        "clone_order_number": po.order_number
    }

    header = {'Authorization': 'Bearer ' + getToken(),
                  'Content-Type': 'application/json'}
    SAVR_ORDER_URL = settings.MG_ROOT_URL + "/rest/V1/carts/mine/savecart"

    # # 检查库存或产品是否存在
    # prd_info_json = getPrdBysku(dic_order_info['frame_sku'])
    # # 重做数量
    # reorder_qty = dic_order_info['quantity']
    #
    # prd_info = json.loads(prd_info_json)
    # if prd_info.has_key('extension_attributes') and prd_info['extension_attributes'].has_key('stock_item'):
    #     stock_qty = prd_info['extension_attributes']['stock_item']['qty']
    #
    #     logging.debug("库存数量：%s" % stock_qty)
    #     f.write("\n========2.请求产品库存数量=================\n")
    #     f.write("库存数量：%s" % stock_qty)
    #     f.write("\n========请求产品数量=================\n")
    #     if stock_qty <= 0:
    #         ret = {
    #             "status": -1,
    #             "url": "",
    #             "message": "此镜架已经没有库存",
    #         }
    #         return HttpResponse(json.dumps(ret))
    #
    #     if (stock_qty - int(reorder_qty) < 0):
    #         ret = {
    #             "status": -1,
    #             "url": "",
    #             "message": "库存数量不足，剩余库存数量:%s" % stock_qty,
    #         }
    #         return HttpResponse(json.dumps(ret))
    #
    # else:
    #     f.write("\n========2.请求产品数量结果=================\n")
    #     f.write(prd_info_json)
    #     f.write("\n========请求产品数量=================\n")
    #     ret = {
    #         "status": -1,
    #         "url": "",
    #         "message": prd_info.get('message', '')
    #     }
    #     return HttpResponse(json.dumps(ret))
    pocs = RemakeOrderCart.objects.filter(order_number=order_number,is_remake=0)
    temp_json_order_dict = append_glasses_item(dic_order,pocs,order_number,freight_amount)
    json_order = json.dumps({"data": temp_json_order_dict}, cls=DateEncoder)
    f.write("\n========6.订单请求对象============\n")
    f.write(json_order)
    f.write("\n========订单请求对象结束============\n")
    api_response = requests.post(SAVR_ORDER_URL, data=json_order, headers=header, timeout=60, verify=False)
    f.write("\n========订单返回对象============\n")
    f.write(api_response.text)
    api_response_dict = json.loads(api_response.text)
    if api_response_dict.has_key("entity_id"):
        sales_order_id = api_response_dict.get('entity_id')
        f.write("订单id%s" % str(sales_order_id))
        f.write("\n========订单返回对象结束============\n")
        state = AuthCode.encode_ex(str(sales_order_id))
        success_order_url = settings.MG_ROOT_URL + "/checkout/onepage/success/" + "?state=" + state
        ret = {
            "status": 0,
            "url": success_order_url,
            "message": "Success!",
        }
        # 成功后加入reorder订单
        reorder_number = api_response_dict.get('increment_id')
        for poc in pocs:
            # 写入重做单表
            remake = RemakeOrder()
            remake.item_id = poc.item_id
            remake.order_number = order_number
            remake.remake_order = reorder_number
            remake.user_id = request.user.id
            remake.user_name = request.user.username
            remake.save()

            poc.remake_order = reorder_number
            poc.is_remake = 1
            poc.save()

        # 修改主表（兼容之前）
        f.write("\n========7.保存pgorder的reorder number============\n")
        pg_order = PgOrder.objects.get(order_number=order_number)
        if (pg_order.reorder_number):
            pg_order.reorder_number = pg_order.reorder_number + ";" + reorder_number
        else:
            pg_order.reorder_number = reorder_number
        pg_order.save()
        f.write("\n========7.保存pgorder的reorder number结束============\n")
        print(json.dumps(ret))
        return HttpResponse(json.dumps(ret))
    else:
        f.write("\n========订单返回对象错误============\n")
        ret = {
            "status": -1,
            "url": "",
            "message": api_response.text,
        }
        return HttpResponse(json.dumps(ret))

def reorder_del_cart(request):
    dic_order_info = json.loads(request.body)
    id = dic_order_info.get('cart_id','')
    if(id):
        RemakeOrderCart.objects.filter(id=id,is_remake=0).delete()
        ret = {
            "status":0,
            "msg":"此眼镜的重做信息已删除！"
        }
    else:
        ret = {
            "status": -1,
            "msg": "请求参数出错！"
        }
    return  HttpResponse(json.dumps(ret))

#生成订单
def reorder_add_to_cart(request):
    f = open("reorder.txt", 'a')
    dic_order_info = json.loads(request.body)
    f.write("\n========1.请求信息=================\n")
    f.write(request.body)
    f.write("\n========请求信息=================\n")

    item_id = dic_order_info['item_id']
    poi = PgOrderItem.objects.filter(item_id=item_id)[0]

    shipping_info = dic_order_info.get('shipping_method','')
    list_shipping_method = DICT_SHIPPING_METHODS[poi.pg_order_entity.country_id]
    k = [val for val in list_shipping_method if val['id'] == shipping_info]
    if(len(k)>0):
        shipping_description = k[0]['description']
        shipping_method = k[0]['id']
    else:
        shipping_description = poi.pg_order_entity.shipping_description
        shipping_method = poi.pg_order_entity.shipping_method

    payment_method = ''
    try:
        PaymentInfo = get_order_info(poi.order_number)
        payinfo = json.loads(PaymentInfo)
        payment_method = payinfo['items'][0]['payment']['method']
    except Exception as e:
        payment_method = 'stripecreditcards'
        f.write("\n========获取支付信息失败================\n")
        f.write(str(e))

    freight_amount = 0.00

    print("----------1------------------------")
    try:
        header = {'Authorization': 'Bearer ' + getToken(),
                  'Content-Type': 'application/json'}
        SAVR_ORDER_URL = settings.MG_ROOT_URL + "/rest/V1/carts/mine/savecart"
        #修改验光单
        save_profile_rx_url = settings.MG_ROOT_URL + '/prescription/open/update?1=1'
        save_glasses_rx_url = settings.MG_ROOT_URL + '/rest/V1/carts/mine/saveprescription'
        add_profile_url = settings.MG_ROOT_URL + '/rest/V1/profile/add/profile'
        #新增验光单
        add_profile_rx_url = settings.MG_ROOT_URL + '/rest/V1/prescription/add/prescription'
        #检查库存或产品是否存在
        prd_info_json = getPrdBysku(dic_order_info['frame_sku'])
        #重做数量
        reorder_qty = dic_order_info['quantity']
        prd_info = json.loads(prd_info_json)
        if prd_info.has_key('extension_attributes') and prd_info['extension_attributes'].has_key('stock_item'):
            stock_qty = prd_info['extension_attributes']['stock_item']['qty']

            logging.debug("库存数量：%s"%stock_qty)
            f.write("\n========2.请求产品库存数量=================\n")
            f.write("库存数量：%s"%stock_qty)
            f.write("\n========请求产品数量=================\n")
            if stock_qty <=0:
                ret = {
                    "status": -1,
                    "url": "",
                    "message": "此镜架已经没有库存",
                }
                return HttpResponse(json.dumps(ret))

            if(stock_qty-int(reorder_qty)<0):
                ret = {
                    "status": -1,
                    "url": "",
                    "message": "库存数量不足，剩余库存数量:%s"%stock_qty,
                }
                return HttpResponse(json.dumps(ret))

        else:
            f.write("\n========2.请求产品数量结果=================\n")
            f.write(prd_info_json)
            f.write("\n========请求产品数量=================\n")
            ret = {
                "status": -1,
                "url": "",
                "message": prd_info.get('message','')
            }
            return HttpResponse(json.dumps(ret))
        if(dic_order_info['profile_prescription']['prescription_type']!='N'):
            print("=============poi.is_nonPrescription:%s,item_id:%s==========="%(poi.is_nonPrescription,poi.item_id))
            # 如果是non-rx转换过来的验光单，需要请求接口，并检查是否有profile，如果没有profile则先生成profile
            if poi.is_nonPrescription:
                req_profile_prescription = dic_order_info['profile_prescription']
                req_profile_prescription['exam_date'] = "01/01/1970"
                req_profile_prescription['expire_date'] = "01/01/1970"
                if(poi.profile_id):
                    req_profile_prescription['prescription_name']=poi.profile_name
                    req_profile_prescription['profile_id']=poi.profile_id
                else:
                    data = {"data":{"customer_id":poi.pg_order_entity.customer_id,"nickname":"New Name"}}
                    results = requests.post(add_profile_url, data=json.dumps(data),headers=header, timeout=60, verify=False)
                    profile = json.loads(results.text)
                    if profile.get("status") == 0:
                        req_profile_prescription['profile_id'] = profile['data']['profile_id']
                        req_profile_prescription['prescription_name'] = "New Name"
                    else:
                        ret = {"status": -1, "msg": "生成profile出错！！！"}
                        return HttpResponse(json.dumps(ret))

                results = requests.post(add_profile_rx_url, data=json.dumps({"data":req_profile_prescription}), headers=header, timeout=60,
                                        verify=False)
                new_rx = json.loads(results.text)
                if(new_rx['status']==0):
                    req_profile_prescription['entity_id']=new_rx['data']['profile_prescription_id']
                    print("=================新增验光单==================")
                    print(json.dumps({"data": req_profile_prescription}))
                else:
                    return HttpResponse({"status": -1,"message":"新增验光单失败"})
                profile_prescription = req_profile_prescription
            else:
                # 看是否修改了原始验光单，如果是则返回新的原始验光单ID，glasses验光单ID
                result = is_rx_updated(poi, dic_order_info)

                f.write("\n========3.对比验光单接口=================\n")
                f.write(json.dumps(result,cls=DateEncoder))
                f.write("\n========对比验光单接口结束=================\n")

                if(result["status"] == -1):
                    ret = {"status": -1, "msg": "原始验光单不存在！！！"}
                    return HttpResponse(json.dumps(ret))
                logging.debug(json.dumps(result['rx']))
                req_profile_prescription = result['rx']

                if (req_profile_prescription.get('prescription_name', '')):
                    req_profile_prescription['prescription_name'] = getParmTrans(req_profile_prescription['prescription_name'])

                # req_profile_prescription = json.loads(json.dumps(req_profile_prescription,cls=DateEncoder).replace("&#x27;", "'"))
                params_url = ""
                # 处理特殊字符
                for i in dict_generator(req_profile_prescription):
                    params_url = params_url+ "&" + i[0] + ']['.join(i[1:-1])  + '=' + str(i[-1])
                f.write("\n========4.请求修改验光单链接=================\n")
                f.write(save_profile_rx_url+params_url)
                f.write('\n')
                # print("--------------------save_profile_rx_url+params_url---------------------------------------")
                # print(save_profile_rx_url+params_url)
                # print(json.dumps(req_profile_prescription))
                results = requests.post(save_profile_rx_url+params_url, data=json.dumps(req_profile_prescription), headers=header, timeout=60, verify=False)
                obj_profile_prescription = json.loads(results.text)
                if(obj_profile_prescription['status'] == True):
                    profile_prescription = obj_profile_prescription['data']
                else:
                    ret= {"status":-1,"msg":"修改验光单失败！！！"}
                    return HttpResponse(json.dumps(ret))
                # profile_prescription = {"origin_rx":temp_profile_prescrition['rx'],"new_prescription_rx":results.text}
                f.write("\n========请求修改验光单结果=================\n")
                f.write(results.text)

            print("====================2222=========================")
            # 保存glasses 验光单
            glasses_rx_dict = dic_order_info['prescription']
            if poi.is_nonPrescription:
                glasses_rx_dict['prescription_name'] ="New Name"

            if (glasses_rx_dict.has_key("entity_id")):
                glasses_rx_dict.pop('entity_id')

            f.write("\n========5.请求glasse验光单信息================\n")
            f.write(json.dumps(glasses_rx_dict))
            glasses_rx_result = requests.post(save_glasses_rx_url, data=json.dumps(glasses_rx_dict), headers=header,
                                               timeout=60, verify=False)

            f.write("\n========返回glasse验光单信息================\n")
            f.write(glasses_rx_result.text)
            glasses_prescription = json.loads(glasses_rx_result.text)
            if glasses_prescription.get('entity_id',''):
                f.write("\n========新的glasses验光单ID信息=================\n")
                f.write("glasses_prescription_id:%s" % glasses_prescription.get('entity_id',''))
            else:
                f.write("\n========新的glasses验光单生成失败???=================\n")
                ret = {
                    "status": -1,
                    "url": "",
                    "message": "生成glasses验光单出错！",
                }
                return HttpResponse(json.dumps(ret))

            print("====================1113=========================")
            # 生成item
            save_result = gennerate_glasses_item(request,dic_order_info, poi,False,profile_prescription, glasses_prescription)
            f.write("\n========请求glasse验光单信息结束================\n")
        else:
            save_result =  gennerate_glasses_item(request,dic_order_info, poi, True, None, None)
        return HttpResponse(json.dumps(save_result))

    except Exception as e:
        ret = {
            "status": -1,
            "url": "",
            "message": format(e),
        }
        return HttpResponse(json.dumps(ret))


# 插入明细
def gennerate_glasses_item(request,dic_order_info,poi,is_norx,profile_prescrition,glasses_prescrition):
    try:
        if(is_norx == False):
            print(profile_prescrition)
            print(glasses_prescrition)
            profile_prescrition_id = profile_prescrition['entity_id']
            glasses_prescrition_id = glasses_prescrition['entity_id']
        else:
            profile_prescrition_id = None
            glasses_prescrition_id = None

        roc = RemakeOrderCart.objects.filter(order_number=poi.order_number)
        # 假定一个购物车IETM_ID，用该订单的id值作为item id
        parent_item = (len(roc)+1)*10
        item_info ={}
        #需要取出镜架价格
        prd_info_json = getPrdBysku(dic_order_info['frame_sku'])
        reorder_qty = int(dic_order_info['quantity'])
        # print("---------------stock sku---------------------------")
        prd_info =json.loads(prd_info_json)
        # print("---------------stock sku---------------------------")
        frame_id = prd_info['id']
        frame_sku = prd_info.get('sku')
        frame_name = prd_info.get('name')
        frame_final_price = get_prd_final_price(prd_info)
        frame_price = str(compare_price(prd_info.get('price'),frame_final_price))
        if (profile_prescrition_id and glasses_prescrition_id):
            info_buyRequest = {"simple_sku":frame_sku,"info_buyRequest":json.dumps(dic_order_info,cls=DateEncoder)}
        else:
            info_buyRequest = json.dumps({"simple_sku":frame_sku,"info_buyRequest":dic_order_info,"is_nonPrescription":1},cls=DateEncoder)
        #php 序列化对象
        info_buyRequest = phpserialize.dumps(info_buyRequest)

        try:
            image_url = prd_info['media_gallery_entries'][0]['file']
        except:
            image_url = ''

        # 如果验光单变化需要重新获取
        profile_id = poi.profile_id
        frame_info ={
            "sku":frame_sku,
            "store_id": 1,
            "name":frame_name,
            "qty_ordered": reorder_qty,
            "qty_invoiced": reorder_qty,
            "price":frame_price,
            "img_url":image_url,
            "img_host":settings.MG_ROOT_URL,
            "base_price": frame_price,
            "row_total": frame_price,
            "base_row_total": frame_price,
            "price_incl_tax": frame_price,
            "base_price_incl_tax": frame_price,
            "row_total_incl_tax": frame_price,
            "base_row_total_incl_tax": frame_price,
            "original_price": frame_price,

            "base_original_price": frame_price,
            "product_id": frame_id,
            "profile_id": profile_id,
            #如果验光单变化需要重新获取，并重新编辑验光单
            "profile_prescription_id": profile_prescrition_id,
            "glasses_prescription_id": glasses_prescrition_id,
            "product_type": 'simple',
            "free_shipping": False,
            "row_weight": prd_info.get("weight"),
            "weight": prd_info.get("weight"),
            "is_qty_decimal": False,
            "quote_item_id": 2,
            "parent_item": parent_item,
            "is_virtual": "0",
            "applied_rule_ids": "",
            "additional_data": "",
            "tax_percent": 0,
            "tax_amount": 0,
            "base_tax_amount": 0,
            "discount_tax_compensation_amount": 0,
            "base_discount_tax_compensation_amount": 0,
            "discount_percent": 0,
            "discount_amount": 0,
            "base_discount_amount": 0,
            "has_children": True,
            "is_php": 0
        }

        item_info[0] = ""
        item_info[1] = frame_info
        i = 2
        item_count = 0
        row_total = 0.00
        base_row_total = 0.00
        price = 0.00
        weight = 0.00
        for lens in dic_order_info['orderglass']:
            #获取产品信息
            prd_dict = dic_order_info['orderglass'][lens]
            prd_info_json = getPrdBysku(prd_dict['sku'])
            child_prd_info = json.loads(prd_info_json)
            prd_id = child_prd_info['id']
            prd_sku = child_prd_info['sku']
            origin_prd_price = child_prd_info['price']
            prd_final_price = get_prd_final_price(child_prd_info)
            prd_price = str(compare_price(origin_prd_price, prd_final_price))
            prd_name = child_prd_info['name']
            prd_type_id = child_prd_info['type_id']
            #有的产品没有重量
            prd_weight = child_prd_info.get('weight',0)

            orderglass_info = {
                "sku": prd_sku,
                "name": prd_name,
                "weight": prd_weight,
                "is_qty_decimal": False,
                "qty_ordered": reorder_qty,
                "qty_invoiced":reorder_qty,
                "quote_item_id": i+1,
                "parent_item": parent_item,
                "original_price": prd_price,
                "price": prd_price,
                "base_price": "0.0000",
                "tax_percent": "0.0000",
                "tax_amount": "0.0000",
                "row_weight": 0,
                "row_total": prd_price,
                "base_original_price": prd_price,
                "base_tax_amount": "0.0000",
                "base_row_total": prd_price,
                "store_id": 1,
                "product_id": prd_id,
                "is_virtual": "1",
                "product_type": prd_type_id,
                "profile_id": profile_id,
                "profile_prescription_id": profile_prescrition_id,
                "glasses_prescription_id": glasses_prescrition_id,
                "free_shipping": "0",
                "discount_percent": "0.0000",
                "discount_amount": "0.0000",
                "base_discount_amount": "0.0000",
                "gift_message_available": "0"
            }
            # -------------------------------
            price = round(price + float(orderglass_info.get('price',0.00)),2)
            row_total = row_total + round(float(orderglass_info.get('row_total',0.00)),2)
            base_row_total = base_row_total + round(float(orderglass_info.get('base_row_total',0.00)),2)
            weight = weight + round(float(orderglass_info.get('weight',0.00)),2)
            # -------------------------------
            i = i+1
            item_count = item_count +1
            item_info[i] = orderglass_info

        base_price = price
        sum_row_total = round(row_total + float(frame_info.get('row_total', 0.00)),2) * reorder_qty
        sum_weight = weight + round(float(frame_info.get('weight', 0.00)),2) * reorder_qty
        sum_item_price = round(price + float(frame_info.get('price', 0.00)), 2)* reorder_qty
        discount_amount = 0-sum_item_price

        #获取镜架颜色
        color_list = [val for val in prd_info['custom_attributes'] if val['attribute_code'] == "color"]
        # 获取镜架颜色
        try:
            color_value_id = color_list[0]['value']
            str_frame_color = get_color_list('color')
            obj_frame_color = json.loads(str_frame_color)
            color_value_list = [val for val in obj_frame_color['items'][0]['options'] if val['value'] == color_value_id]
            color_value = color_value_list[0]['label']
        except Exception as e:
            #无颜色值生成订单报错
            color_value = color_list[0]['value']
        prd_info1 = {
            "sku": prd_info.get('sku'),
            "store_id": 1,
            "quote_item_id": parent_item,
            "name": frame_name,
            "qty_ordered": reorder_qty,
            "qty_invoiced": reorder_qty,
            "price": sum_item_price,

            "base_price": sum_item_price,
            "row_total": sum_row_total,
            "base_row_total": sum_row_total,
            "price_incl_tax": sum_row_total,
            "base_price_incl_tax": sum_row_total,
            "row_total_incl_tax": sum_row_total,
            "base_row_total_incl_tax": sum_row_total,
            "base_original_price": frame_price,
            "product_id": frame_id,
            "original_price": frame_price,
            "profile_id": poi.profile_id,
            "profile_prescription_id": profile_prescrition_id,
            "glasses_prescription_id": glasses_prescrition_id,
            "product_type": "configurable",
            "free_shipping": False,
            "row_weight": sum_weight,
            "weight": sum_weight,
            "is_qty_decimal": 0,

            "is_virtual": "0",
            "applied_rule_ids": "",
            "additional_data": "",
            "tax_percent": 0,
            "tax_amount": 0,
            "base_tax_amount": 0,
            "discount_tax_compensation_amount": 0,
            "base_discount_tax_compensation_amount": 0,
            "discount_percent": 100,
            "discount_amount": discount_amount,
            "base_discount_amount": 0,
            "product_options": {
                "info_buyRequest":info_buyRequest,#checkout_params====待获取
                "attributes_info": [{
                    "label": "Color",
                    "value":color_value,
                }],
                "simple_name": frame_name,
                "simple_sku": frame_sku,
                "product_calculations": 1,
                "shipment_type": 0
            },
            "has_children": True
        }
        item_info[0] = prd_info1
        #保存重做信息
        roc = RemakeOrderCart()
        roc.is_norx= is_norx
        roc.original_profile_prescription_id = poi.profile_prescription_id
        # roc.original_glasses_prescription_id = poi

        roc.is_norx= is_norx
        roc.profile_prescription_options = json.dumps(profile_prescrition)
        roc.glasses_prescription_options = json.dumps(glasses_prescrition)
        roc.glasses_prescription_id = glasses_prescrition_id

        roc.profile_prescription_id = profile_prescrition_id
        roc.profile_id = profile_id
        roc.item_options = json.dumps(item_info)
        roc.item_id = poi.item_id
        roc.is_remake = 0
        roc.items_count = 2
        roc.order_number = poi.order_number
        roc.user_id =  request.user.id
        roc.user_name = request.user.username
        roc.save()
        return {"status": 0, "message": "%s(%s)重做信息保存成功！！"%(poi.name,poi.frame)}
    except Exception as e:
        return {"status": -1,  "message": format(e)}

#格式化字符串中特殊的字符
def getParmTrans(data):
    if type(data) == unicode:
        data = data.encode("utf-8")
    if isinstance(data, bool):
        return data
    else:
        return urllib.quote(data)

def request_rules(request, port):
    '''
        请求Rules服务器的3002接口
        :param request:
        :return:
        '''
    # from util.response import *
    rm = response_message()
    dh = dict_helper()

    if request.method == 'POST':
        try:
            request_body = request.body
            #处理单引号字符
            request_body = request_body.replace("&#x27;", "'")
            req_json = json.loads(request_body)
            prescription = req_json['parameters']['prescription']
            if(prescription.get('prescription_name','')):
                prescription['prescription_name']= getParmTrans(prescription['prescription_name'])
            # url_part = 'api/v4.0/rule/%s/' % port
            # req_url = settings.PG_RULES_BASE_URL + url_part
            # logging.debug(req_url)

            # headers = {'Content-Type': 'application/json'}
            # req = urllib2.Request(url=req_url, data=req_str, headers=headers)

            try:
                # res = urllib2.urlopen(req)
                # logging.debug(res)
                # res_data = res.read()

                sku = req_json['parameters']['product']['sku']
                reorder_qty = req_json['parameters']['product']['quantity']

                # 检查库存或产品是否存在
                prd_info_json = getPrdBysku(sku)
                prd_info = json.loads(prd_info_json)
                # print("---------------stock sku---------------------------")
                if prd_info.has_key('extension_attributes') and prd_info['extension_attributes'].has_key('stock_item'):
                    stock_qty = prd_info['extension_attributes']['stock_item']['qty']
                    is_in_stock = prd_info['extension_attributes']['stock_item']['is_in_stock']
                    logging.debug("is_in_stock:%s"%is_in_stock)
                    if stock_qty <= 0 or is_in_stock==False :
                        ret = {
                            "status": -1,
                            "url": "",
                            "message": "镜架没有库存或已处于下架状态",
                        }
                        return HttpResponse(json.dumps(ret))

                    if stock_qty - int(reorder_qty) < 0:
                        ret = {
                            "status": -1,
                            "url": "",
                            "message": "库存数量不足，当前库存数量为:%s"%stock_qty,
                        }
                        return HttpResponse(json.dumps(ret))

                else:
                    ret = {
                        "status": -1,
                        "url": "",
                        "message": prd_info.get('message', '')
                    }
                    return HttpResponse(json.dumps(ret))



                if port in[3001,3002]:
                    logging.debug("==============begin %s========================"%port)
                    url = settings.MG_ROOT_URL+'/buy/index/api/sku/%s?lens-color-type=clear'%sku
                elif port == 3009:
                    url = settings.MG_ROOT_URL+'/buy/index/apiCustomize/sku/%s/?1=1'%sku

                logging.debug("==============request%s========================")
                logging.debug("==============request url%s========================" % url)
                params_url = ""
                # k = 0
                for i in dict_generator(req_json):
                    # if k == 0:
                    #     params_url = i[0] + '[' + ']['.join(i[1:-1]) + ']' + '=' + str(i[-1])
                    # else:
                    params_url += "&" + i[0] + '[' + ']['.join(i[1:-1]) + ']' + '=' + str(i[-1])
                    # k = k + 1
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
                }
                r = requests.post(url + params_url, json.dumps(req_json), headers=headers,timeout=60, verify=False)
                logging.debug("==============end port%s========================"%port)
                return  HttpResponse(r.text)

                # logging.debug('准备转换成叶子节点 ....')
                # res_data = json.loads(res_data)
                # leaves_items = res_data['body']['recommended']
                # logging.debug(leaves_items)
                #
                # sl = SearchLeaves(res_data)
                # lst = sl.search_key('is_leaf', 1)
                #
                # resp = {}
                # resp['body'] = res_data['body']
                # resp['body']['recommended'] = lst
                # res_data = json.dumps(resp)
                # logging.debug(res_data)
                # return HttpResponse(res_data)
            except Exception as e:
                # m.capture_execption(e)
                logging.debug(e.message)
                rm.code = -1
                rm.message = e.message

            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            return HttpResponse(json_body)
        except Exception as e:
            # rm.capture_execption(e)
            rm.code = -1
            rm.message = e.message
            logging.debug(e.message)

        logging.debug(rm.__dict__)
        json_body = dh.convert_to_dict(rm)
        logging.debug(json_body)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)
    else:
        rm.code = 400
        rm.message = "Not support Get method!"
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)


@csrf_exempt
def redirect_api_reorder_rules_3002(request):
    '''
    请求Rules服务器的3002接口
    :param request:
    :return:
    '''
    return request_rules(request, 3002)


@csrf_exempt
def redirect_api_reorder_rules_3002(request):
    '''
    请求Rules服务器的3002接口
    :param request:
    :return:
    '''
    return request_rules(request, 3002)


@csrf_exempt
def redirect_api_reorder_rules_3001(request):
    '''
    请求Rules服务器的3002接口
    :param request:
    :return:
    '''
    return request_rules(request, 3001)


@csrf_exempt
def redirect_api_reorder_rules_3009(request):
    '''
    请求Rules服务器的3002接口
    :param request:
    :return:
    '''
    return request_rules(request, 3009)\


@csrf_exempt
def redirect_api_web_order(request):
    '''
    生成网站订单接口
    :param request:
    :return:
    '''
    return gennerate_web_order(request)


@csrf_exempt
def redirect_api_add_to_cart(request):
    '''
    重做单加入购物车
    :param request:
    :return:
    '''
    return reorder_add_to_cart(request)

@csrf_exempt
def redirect_api_del_cart(request):
    '''
    重做单加入购物车
    :param request:
    :return:
    '''
    return reorder_del_cart(request)


@csrf_exempt
def redirect_api_verification_prescription(request):
    '''
    2020.01.17 by guof. OMS-588
    验光单校验接口
    :param request:
    :return:
    '''
    from util.response import *
    rm = response_message()
    dh = dict_helper()
    if request.method == 'POST':
        try:
            logging.debug('----------------------------------------------------------------------')
            logging.debug('request method: %s' % request.method)
            logging.debug('----------------------------------------------------------------------')

            logging.debug(request.body)

            req_json = json.loads(request.body)

            url_part = 'prescription/open/update'
            req_url = settings.BASE_URL + url_part
            logging.debug(req_url)

            req_str = json.dumps(req_json)

            headers = {'Content-Type': 'application/json'}
            req = urllib2.Request(url=req_url, data=req_str, headers=headers)

            try:
                res = urllib2.urlopen(req)
                logging.debug(res)
                res_data = res.read()
                # logging.debug(res_data)
                return HttpResponse(res_data)
            except Exception as e:
                # m.capture_execption(e)
                logging.debug(e.message)
                rm.code = -1
                rm.message = e.message

            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            return HttpResponse(json_body)
        except Exception as e:
            # rm.capture_execption(e)
            rm.code = -1
            rm.message = e.message
            logging.debug(e.message)

        logging.debug(rm.__dict__)
        json_body = dh.convert_to_dict(rm)
        logging.debug(json_body)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)
    else:
        rm.code = 400
        rm.message = "Not support Get method!"
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)


class UploadFile(APIView):
    def post(self, request, format=None):
        try:
            data = {}
            data_dict = {}
            form_data = request.data
            vca_file = form_data.get('file', None)
            vca_data = form_data.get('data', '')
            product_sku = form_data.get('product_sku', '')
            vca_file_name = vca_file.name
            from util.uploadfile_util import UploadFile
            from pg_oms.settings import VCA_MEDIA_SERVER
            from wms.models import ProductFrameVca, HistoryFrameVca
            nowdate = datetime.datetime.now().strftime('%Y-%m-%d')
            batch_number = datetime.datetime.now().strftime('%Y%m%d')
            date_list = nowdate.split("-")
            year = date_list[0]
            month = date_list[1]
            day = date_list[2]
            name, extension = vca_file.name.split(".")
            upload_path = VCA_MEDIA_SERVER.get('UPLOAD_MEDIA_BASE', '')
            if upload_path == '':
                return JsonResponse(data='', code=400, msg='请配置存储位置', status=status.HTTP_400_BAD_REQUEST)
            make_dir_day = upload_path + 'vca/' + name + '/' + year + '/' + month + "/" + day
            uploadfile = UploadFile()
            json_data = uploadfile.upload_file(make_dir_day, vca_file, 'LOCAL')
            if json_data['code'] == 0:
                product_frame_vcas = ProductFrameVca.objects.filter(product_num=product_sku)
                if len(product_frame_vcas) > 0:
                    product_frame_vca = product_frame_vcas[0]
                    history_frame_vca = HistoryFrameVca()
                    history_frame_vca.batch_number = product_frame_vca.batch_number
                    history_frame_vca.frame = product_frame_vca.product_num
                    history_frame_vca.file_path = product_frame_vca.file_path
                    history_frame_vca.property_list = product_frame_vca.property_list
                    history_frame_vca.save()

                    product_frame_vca.file_path = json_data['url']
                    product_frame_vca.property_list = vca_data
                    product_frame_vca.product_num = product_sku
                    product_frame_vca.save()
                else:
                    product_frame_vca = ProductFrameVca()
                    product_frame_vca.file_path = json_data['url']
                    product_frame_vca.property_list = vca_data
                    product_frame_vca.product_num = product_sku
                    product_frame_vca.batch_number = batch_number
                    product_frame_vca.save()
                return JsonResponse(data=data, code=200, msg="执行成功", status=status.HTTP_200_OK)
            else:
                return JsonResponse(data='', code=400, msg=json_data['msg'], status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=e, status=status.HTTP_400_BAD_REQUEST)


class QcGlassesFirstInspection(APIView):
    def post(self, request, format=None):
        try:
            form_data = request.data
            json_obj = form_data.get('json_obj', '')
            from qc.models import PreliminaryPrescripitonActual
            pa = PreliminaryPrescripitonActual()
            pa.od_sph = json_obj['prescription_actual']['od_sph'] if json_obj['prescription_actual']['od_sph']!= '' else '0.00'
            pa.od_cyl = json_obj['prescription_actual']['od_cyl'] if json_obj['prescription_actual']['od_cyl']!= '' else '0.00'
            pa.od_axis = json_obj['prescription_actual']['od_axis'] if json_obj['prescription_actual']['od_axis']!= '' else '0.00'
            pa.od_add = json_obj['prescription_actual']['od_add'] if json_obj['prescription_actual']['od_add']!= '' else '0.00'
            pa.od_pd = json_obj['prescription_actual']['od_pd'] if json_obj['prescription_actual']['od_pd']!= '' else '0.00'
            pa.od_prism = json_obj['prescription_actual']['od_prism'] if json_obj['prescription_actual']['od_prism']!= '' else '0.00'
            pa.od_base = json_obj['prescription_actual']['od_base']

            pa.os_sph = json_obj['prescription_actual']['os_sph'] if json_obj['prescription_actual']['os_sph']!= '' else '0.00'
            pa.os_cyl = json_obj['prescription_actual']['os_cyl'] if json_obj['prescription_actual']['os_cyl']!= '' else '0.00'
            pa.os_axis = json_obj['prescription_actual']['os_axis'] if json_obj['prescription_actual']['os_axis']!= '' else '0.00'
            pa.os_add = json_obj['prescription_actual']['os_add'] if json_obj['prescription_actual']['os_add']!= '' else '0.00'
            pa.os_pd = json_obj['prescription_actual']['os_pd'] if json_obj['prescription_actual']['os_pd']!= '' else '0.00'
            pa.os_prism = json_obj['prescription_actual']['os_prism'] if json_obj['prescription_actual']['os_prism']!= '' else '0.00'
            pa.os_base = json_obj['prescription_actual']['os_base']
            pa.pd = json_obj['prescription_actual']['pd'] if json_obj['prescription_actual']['pd']!= '' else '0.00'
            pa.is_singgle_pd = json_obj['prescription_actual']['is_singgle_pd']
            pa.lab_number = json_obj['lab_number']
            pa.comments = json_obj['last_error']
            pa.user_name = json_obj['login_info']['Username']
            pa.user_id = json_obj['login_info']['AdminId']
            pa.save()
            return JsonResponse(data='', code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=400, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SetGlassesWeight(APIView):
    def post(self, request, format=None):
        try:
            form_data = request.data
            json_obj = form_data.get('json_obj', '')
            now_date = datetime.datetime.now()
            lab_number = json_obj['lab_number']
            if lab_number == '':
                return JsonResponse(data='', code=400, msg='Lab Number 不能为空', status=status.HTTP_400_BAD_REQUEST)

            labs = LabOrder.objects.filter(lab_number=lab_number)
            if len(labs) == 0:
                return JsonResponse(data='', code=400, msg='LabOrder 未找到', status=status.HTTP_400_BAD_REQUEST)

            lab = labs[0]
            lab.weight = json_obj['lab_data']['weight']
            lab.gross_weight = json_obj['lab_data']['gross_weight']
            lab.weight_create_at = now_date
            lab.operator_id = json_obj['login_info']['AdminId']
            lab.operator_name = json_obj['login_info']['Username']
            lab.save()
            return JsonResponse(data='', code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=500, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetFrameVca(APIView):
    def post(self, request, format=None):
        try:
            data = {}
            form_data = request.data
            product_sku = form_data.get('product_sku', '')

            if product_sku == '':
                return JsonResponse(data='', code=400, msg='SKU 不能为空', status=status.HTTP_400_BAD_REQUEST)

            product_frame_vcas = ProductFrameVca.objects.filter(product_num=product_sku)
            if len(product_frame_vcas) == 0:
                return JsonResponse(data='', code=400, msg='VCA 未找到', status=status.HTTP_200_OK)

            product_frame_vca = product_frame_vcas[0]
            data['product_num'] = product_frame_vca.product_num
            data['property_list'] = product_frame_vca.property_list
            data['file_path'] = product_frame_vca.file_path
            return JsonResponse(data=data, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=500, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetLaborderData(APIView):
    def post(self, request, format=None):
        try:
            data_list = []
            form_data = request.data
            create_at = form_data.get('create_at', '')
            push_flag = form_data.get('push_flag', '')

            if create_at == '':
                return JsonResponse(data='', code=400, msg='时间不能为空', status=status.HTTP_400_BAD_REQUEST)

            if push_flag == '':
                return JsonResponse(data='', code=400, msg='推送标识不能为空', status=status.HTTP_400_BAD_REQUEST)

            laborders = LabOrder.objects.filter(create_at__gte=create_at, is_push=push_flag)
            print(len(laborders))
            for item in laborders:
                try:
                    fmat = product_frame.objects.filter(sku=item.frame).first().fmat
                except Exception as e:
                    print(e)

                # 镜架类型。 1：塑料，2：金属，3：无框，4：环氧树脂
                if fmat == 'Plastic'or 'Acetate':
                    fmat = '1'
                elif fmat == 'Other Metal' or 'Stainless Steel' or 'Memory Titanium' or 'titanium':
                    fmat == '2'
                elif fmat == 'TR' or 'Ultem':
                    fmat = '4'


                if item.frame_type == 'Full Rim':
                    frame_type = '1'
                elif item.frame_type == 'Rimless':
                    frame_type = '2'
                    fmat = '3'
                elif item.frame_type == 'Semi Rimless' or item.frame_type == 'Semi Rim':
                    frame_type = '3'
                print fmat
                # LTYP 含义：镜片类型： SV:单光，BI:双光， PR：渐进，others：others
                if 'KD' in item.lens_sku:
                    ltyp = 'SV'
                elif 'CP' in item.lens_sku:
                    ltyp = 'BI'
                elif 'CJ' in item.lens_sku:
                    ltyp = 'PR'
                else:
                    ltyp = 'others'


                if item.is_singgle_pd:
                    od_pd = item.pd/2
                    os_pd = item.pd/2
                else:
                    od_pd = item.od_pd
                    os_pd = item.os_pd

                if item.pd == 0 and item.od_pd == 0 and item.os_pd == 0:
                    od_pd = 30
                    os_pd = 30

                data_list.append({
                    'id': item.id,
                    'lab_number': item.lab_number,
                    'create_at': item.create_at,
                    'frame': item.frame,
                    'od_sph': item.od_sph,
                    'os_sph': item.os_sph,
                    'od_cyl': item.od_cyl,
                    'os_cyl': item.os_cyl,
                    'od_axis': item.od_axis,
                    'os_axis': item.os_axis,
                    'od_add': item.od_add,
                    'os_add': item.os_add,
                    'pd': item.pd,
                    'is_singgle_pd': item.is_singgle_pd,
                    'od_pd': item.od_pd,
                    'os_pd': item.os_pd,
                    'od_prism': item.od_prism,
                    'os_prism': item.os_prism,
                    'od_base': item.od_base,
                    'os_base': item.os_base,
                    'od_prism1': item.od_prism1,
                    'os_prism1': item.os_prism1,
                    'od_base1': item.od_base1,
                    'os_base1': item.os_base1,
                    'lab_seg_height': item.lab_seg_height,
                    'assemble_height': item.assemble_height,
                    'sub_mirrors_height': item.sub_mirrors_height,
                    'assemble': 'EPRESS=0\nETYP={0}\nFTYP={1}\nFBFCIN=0.01;0.01\nFBFCUP=0.01;0.01\nLMATTYPE=1;1\nLTYP={2};{3}\nOCHT={4};{5}\nFPINB=0.00;0.00\nPINB=0.00;0.00\nPINBS=0;0\nPOLISH=0\nZTILT=5.6;5.6\nHICRV=0;0\nBEVP=7;7\nIPD={6};{7}\nSPH={8};{9}\nCYL={10};{11}\nAX={12};{13}'.format(frame_type,fmat,ltyp,ltyp, str(item.lab_seg_height), str(item.lab_seg_height),
                                                                                                                                                                                                                                                                                              str(od_pd), str(os_pd), str(item.od_sph),str(item.os_sph),str(item.od_cyl),
                                                                                                                                                                                                                                                                                              str(item.os_cyl), str(item.od_axis), str(item.os_axis))

                })

            return JsonResponse(data=data_list, code=200, msg="执行成功", status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse(data='', code=500, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangeLabOrderIsPush(APIView):
    def post(self, request, format=None):
        try:
            data_list = []
            form_data = request.data
            lab_list = form_data.get('lab_list', [])
            push_flag = form_data.get('push_flag', '')

            if push_flag == '':
                return JsonResponse(data='', code=400, msg='推送标识不能为空', status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    for item in lab_list:
                        LabOrder.objects.filter(lab_number=item).update(is_push=push_flag)
            except Exception as e:
                return JsonResponse(data='', code=400, msg='更新失败', status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse(data=data_list, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=500, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetLaborders(APIView):
    def post(self, request, format=None):
        try:
            data_list = []
            form_data = request.data
            lab_number = form_data.get('lab_number', '')

            if lab_number == '':
                return JsonResponse(data='', code=400, msg='单号不能为空', status=status.HTTP_400_BAD_REQUEST)

            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 0:
                return JsonResponse(data='', code=400, msg='未找到', status=status.HTTP_400_BAD_REQUEST)
            item = lbos[0]
            if item.frame_type == 'Full Rim':
                frame_type = '1'
            elif item.frame_type == 'Rimless':
                frame_type = '2'
            elif item.frame_type == 'Semi Rimless' or item.frame_type == 'Semi Rim':
                frame_type = '3'

            if item.is_singgle_pd:
                od_pd = item.pd/2
                os_pd = item.pd/2
            else:
                od_pd = item.od_pd
                os_pd = item.os_pd

            if item.pd == 0 and item.od_pd == 0 and item.os_pd == 0:
                od_pd = 30
                os_pd = 30

            data_list.append({
                'id': item.id,
                'lab_number': item.lab_number,
                'create_at': item.create_at,
                'frame': item.frame,
                'od_sph': item.od_sph,
                'os_sph': item.os_sph,
                'od_cyl': item.od_cyl,
                'os_cyl': item.os_cyl,
                'od_axis': item.od_axis,
                'os_axis': item.os_axis,
                'od_add': item.od_add,
                'os_add': item.os_add,
                'pd': item.pd,
                'is_singgle_pd': item.is_singgle_pd,
                'od_pd': item.od_pd,
                'os_pd': item.os_pd,
                'od_prism': item.od_prism,
                'os_prism': item.os_prism,
                'od_base': item.od_base,
                'os_base': item.os_base,
                'od_prism1': item.od_prism1,
                'os_prism1': item.os_prism1,
                'od_base1': item.od_base1,
                'os_base1': item.os_base1,
                'lab_seg_height': item.lab_seg_height,
                'assemble_height': item.assemble_height,
                'sub_mirrors_height': item.sub_mirrors_height,
                'assemble': 'EPRESS=0\nETYP={0}\nFTYP=2\nFBFCIN=0.00;0.00\nFBFCUP=0.00;0.00\nLMATTYPE=1;1\nLTYP=SV;SV\nOCHT={1};{2}\nFPINB=0.00;0.00\nPINB=0.00;0.00\nPINBS=0;0\nPOLISH=0\nZTILT=5.6;5.6\nHICRV=0;0\nBEVP=7;7\nIPD={3};{4}\nSPH={5};{6}\nCYL={7};{8}\nAX={9};{10}'.format(frame_type, str(item.lab_seg_height), str(item.lab_seg_height),
                                                                                                                                                                                                                                                                                          str(od_pd), str(os_pd), str(item.od_sph),str(item.os_sph),str(item.od_cyl),
                                                                                                                                                                                                                                                                                          str(item.os_cyl), str(item.od_axis), str(item.os_axis))
            })
            return JsonResponse(data=data_list, code=200, msg="执行成功", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(data='', code=500, msg=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
