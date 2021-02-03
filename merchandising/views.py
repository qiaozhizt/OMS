# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
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

from api.controllers.tracking_controllers import tracking_operation_controller
from oms.models import OperationLog
from wms.models import inventory_operation_log

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

from django.db import connections
from django.db import transaction

import csv
import codecs
import urllib2

from util.db_helper import *
from util.format_helper import *
from util.response import response_message
from util.dict_helper import dict_helper
from const import *

from pg_oms.settings import *


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@csrf_exempt
@login_required
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_category_products_index(request):
    _form_data = {}
    _form_data['request_module'] = 'Merchandising'
    _form_data['request_feature'] = '分类中商品排序'
    items = []
    try:

        page = request.GET.get('page', 1)
        currentPage = int(page)

        items = []
        paginator = Paginator(items, 20)  # Show 20 contacts per page

        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            contacts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            contacts = paginator.page(paginator.num_pages)

        return render(request, "category_products_index.html",
                      {
                          'form_data': _form_data,
                          'filter': filter,
                          'list': contacts,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': reverse('comments'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        _form_data['request_feature'] = 'All Comments'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('comments'),
                      })


@csrf_exempt
@login_required
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_category_products_index_post(request):
    _form_data = {}

    items = []
    positions = []

    if request.method == 'POST':

        try:
            with connections['pg_mg_query'].cursor() as cursor:
                sql = SQL_CATEGORY_PRODUCTS_INDEX
                category_id = request.POST.get('category_id', '6')
                sql = SQL_CATEGORY_PRODUCTS_INDEX % category_id
                logging.info(sql)
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)

                position = {}
                position['position'] = 0
                position['qty'] = 0

                positions.append(position)

                for r in range(len(results)):
                    # logging.debug(r)
                    item = {}
                    item['entity_id'] = results[r].entity_id
                    item['category_name'] = results[r].category_name
                    item['product_id'] = results[r].product_id
                    item['sku'] = results[r].sku
                    item['name'] = results[r].name
                    item['lab_sku'] = results[r].lab_sku
                    item['position'] = results[r].position
                    item['created_at'] = results[r].created_at
                    item['updated_at'] = results[r].updated_at
                    items.append(item)

                    origin_position = positions[len(positions) - 1]
                    if int(origin_position['position']) == int(results[r].position):
                        origin_position['qty'] = int(origin_position['qty']) + 1
                    else:
                        position = {}
                        position['position'] = results[r].position
                        position['qty'] = 1
                        positions.append(position)

            data = {}
            data['json_body'] = items
            data['positions'] = positions

            return HttpResponse(json.dumps(data, cls=DateEncoder))
        except Exception as e:
            return HttpResponse(str(e))

    else:
        return HttpResponse('无效请求')


@csrf_exempt
@login_required
@permission_required('merchandising.REFRESH_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_products_list(request):
    _form_data = {}
    items = []
    _form_data['items'] = items
    try:
        page = request.GET.get('page', 1)
        category_id = request.GET.get('category', 6)
        frame = request.GET.get('frame', '')
        currentPage = int(page)

        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))

        rm = response_message()

        _form_data["request_module"] = "Merchandising"
        _form_data["request_feature"] = "Web 产品清单"

        from .models import ProductListController
        plc = ProductListController()
        rm = plc.GetAll(category_id, frame)
        items = rm.obj
        _form_data['rm'] = rm
        count = len(items)
        if query_string:
            query_string = '&' + query_string
        if count > 0:
            _form_data['total'] = count
        logging.debug("count: %s" % count)
        _form_data["base_url"] = plc.base_url
        paginator = Paginator(items, count)  # Show 20 contacts per page
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        _form_data["items"] = items
        # GET

        return render(request, 'products_list.html', {
            'form_data': _form_data,
            'list': items,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/merchandising/products_list/',
            'query_string': query_string,
        })
    except Exception as ex:
        pass
    return render(request, 'products_list.html', {
        'form_data': _form_data,
        'list': items,
    })


@csrf_exempt
@login_required
@permission_required('merchandising.REFRESH_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_products_list_v1(request):
    _form_data = {}
    items = []
    _form_data['items'] = items
    try:
        page = request.GET.get('page', 1)
        category_id = request.GET.get('category', 6)
        frame = request.GET.get('frame', '')
        min_qty = request.GET.get('min_qty', '')
        max_qty = request.GET.get('max_qty', '')
        cate_type = request.GET.get('cate_type', '')
        _form_data["min_qty"] = min_qty
        _form_data["max_qty"] = max_qty
        _form_data["cate_type"] = cate_type
        currentPage = int(page)
        if category_id == '':
            category_id = 6

        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))

        rm = response_message()

        _form_data["request_module"] = "Merchandising"
        _form_data["request_feature"] = "Web 产品清单"

        from .models import ProductListController
        plc = ProductListController()
        rm = plc.GetAll(category_id, frame, min_qty, max_qty, cate_type)
        items = rm.obj
        _form_data['rm'] = rm
        count = len(items)
        if query_string:
            query_string = '&' + query_string
        if count > 0:
            _form_data['total'] = count
        logging.debug("count: %s" % count)
        _form_data["base_url"] = plc.base_url
        _form_data["product_url"] = plc.product_url
        paginator = Paginator(items, count)  # Show 20 contacts per page
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)
        _form_data["items"] = items
        # GET
        return render(request, 'products_list_v1.html', {
            'form_data': _form_data,
            'list': items,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/merchandising/products_list_v1/',
            'query_string': query_string,
        })
    except Exception as ex:
        pass
    return render(request, 'products_list_v1.html', {
        'form_data': _form_data,
        'list': items,
    })


@csrf_exempt
@login_required
@permission_required('merchandising.REFRESH_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_refresh_product_index(request):
    '''
     刷新产品索引
    :param request:
    :return:
    '''
    rm = response_message()
    dh = dict_helper()
    if request.method == 'POST':
        try:
            requrl = PG_SYNC_API_BASE_URL + PG_SYNC_COMMANDS_URL + PG_SYNC_COMMAND_REFRESH_PRODUCT_INDEX + '/'
            logging.debug(requrl)
            req_data = {}
            req_data['token'] = PG_SYNC_API_TOKEN
            req_data = json.dumps(req_data)
            headers = {'Content-Type': 'application/json'}
            req = urllib2.Request(url=requrl, data=req_data, headers=headers)

            try:
                res = urllib2.urlopen(req)
                logging.debug(res)
                res_data = res.read()
                logging.debug(res_data)
                return HttpResponse(res_data)
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(e.message)

            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            return HttpResponse(json_body)
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(e.message)

            json_body = dh.convert_to_dict(rm)
            json_body = json.dumps(json_body, cls=DateEncoder)
            return HttpResponse(json_body)

    else:
        rm.code = 400
        rm.message = '无效请求'
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)


@csrf_exempt
@login_required
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_shipments_index(request):
    _data = None
    _form_data = {}
    page_info = {}
    _form_data['request_module'] = 'Merchandising'
    _form_data['request_feature'] = '产品出货量查询'

    # POST
    if request.method == 'POST':
        s_info = request.POST.get('info')
        s_page = request.POST.get('page', 1)
        cur_page = int(s_page)
        _data = json.loads(s_info)

        # 拼接SQL
        condition = []
        q_sku = _data.get('sku')
        q_start_date = _data.get('startDate')
        q_end_date = _data.get('endDate')
        q_type_sku = _data.get('sku_type')

        if not q_sku == '':
            condition.append("t0.sku='%s'" % q_sku)
        if not q_start_date == '':
            condition.append("DATE(t0.created_at)>=DATE('%s')" % q_start_date)
        if not q_end_date == '':
            condition.append("DATE(t0.created_at)<=DATE('%s')" % q_end_date)
        if q_type_sku == 'all':
            condition.append("t0.sku REGEXP '.'")
        if q_type_sku == 'frame':
            condition.append("t0.sku REGEXP '^[1-9]'")
        if q_type_sku == 'other':
            condition.append("t0.sku REGEXP '^[a-zA-Z]'")


        # 只筛选自动出库的订单
        condition.append("t0.doc_type='AUTO'")

        # 查询字段
        field_list = ['t0.sku', 'SUM(t0.quantity) AS qty', 't1.quantity', 't2.web_created_at']

        # 联查
        join_list = ['LEFT JOIN wms_inventory_struct t1 ON t0.sku=t1.sku',
                     'LEFT JOIN wms_product_frame t2 ON t0.sku=t2.sku']

        ct = simple_general_query('wms_inventory_delivery t0', field_list, condition, 't0.sku', 'qty', join_list)
        sql = ct.check_sql()
        logging.debug(sql)

        # 查询
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
                logging.debug(results)

                # 分页
                page_date = Paginator(results, 20)
                page_info['cur_page'] = cur_page
                page_info['data_count'] = page_date.count
                page_info['page_count'] = page_date.num_pages
                page_info['prev_page'] = cur_page - 1
                page_info['next_page'] = cur_page + 1
                page_info['left_spnt'] = 0
                page_info['right_spnt'] = 0
                cur_page_data = page_date.page(cur_page)

                # 只显示show_page个页码
                show_page = 5
                half_count = (show_page - 1) / 2
                if page_date.num_pages > show_page:
                    if cur_page <= half_count + 1:
                        page_info['page_range'] = range(1, show_page + 1)
                        page_info['left_spnt'] = 0
                        page_info['right_spnt'] = 1
                    elif cur_page >= page_date.num_pages - half_count:
                        page_info['page_range'] = range(page_date.num_pages - show_page + 1, page_date.num_pages + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 0
                    else:
                        page_info['page_range'] = range(cur_page - half_count, cur_page + half_count + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 1
                else:
                    page_info['page_range'] = range(1, page_date.num_pages + 1)

                return render(request, 'shipments_index_part.html', {
                    'form_data': _form_data,
                    'invds': cur_page_data,
                    'page_info': page_info
                })

        except Exception as e:
            return HttpResponse(e.message)

    # GET
    return render(request, 'shipments_index.html', {
        'form_data': _form_data,
    })


@csrf_exempt
@login_required
@permission_required('merchandising.CATEGORY_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_shipments_index_csv(request):
    s_info = request.GET.get('info')
    _data = json.loads(s_info)

    # 拼接SQL
    condition = []
    q_sku = _data.get('sku')
    q_start_date = _data.get('startDate')
    q_end_date = _data.get('endDate')
    q_type_sku = _data.get('sku_type')

    if not q_sku == '':
        condition.append("t0.sku='%s'" % q_sku)
    if not q_start_date == '':
        condition.append("DATE(t0.created_at)>=DATE('%s')" % q_start_date)
    if not q_end_date == '':
        condition.append("DATE(t0.created_at)<=DATE('%s')" % q_end_date)
    if q_type_sku == 'all':
        condition.append("t0.sku REGEXP '.'")
    if q_type_sku == 'frame':
        condition.append("t0.sku REGEXP '^[1-9]'")
    if q_type_sku == 'other':
        condition.append("t0.sku REGEXP '^[a-zA-Z]'")

    # 只筛选自动出库的订单
    condition.append("t0.doc_type='AUTO'")

    # 查询字段
    field_list = ['t0.sku', 'SUM(t0.quantity) AS qty', 't1.quantity', 't2.web_created_at']

    # 联查
    join_list = ['LEFT JOIN wms_inventory_struct t1 ON t0.sku=t1.sku',
                 'LEFT JOIN wms_product_frame t2 ON t0.sku=t2.sku']

    ct = simple_general_query('wms_inventory_delivery t0', field_list, condition, 't0.sku', 'qty', join_list)
    sql = ct.check_sql()

    # 查询
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)

            response = HttpResponse(content_type='text/csv')
            file_name = 'shipments_index'
            response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
            response.write(codecs.BOM_UTF8)
            writer = csv.writer(response)
            writer.writerow(['产品出货量CSV'])
            writer.writerow(['起始日期', q_start_date, '结束日期', q_end_date])
            writer.writerow([])
            writer.writerow(['产品SKU', '出货数量', '产品库存量', '发售时间'])
            for item in results:
                writer.writerow([item.sku, item.qty, item.quantity, item.web_created_at])
            return response
    except Exception as e:
        return HttpResponse(e.message)


@login_required
@permission_required('merchandising.PRODUCTION_OPERATION_LOG', login_url='/oms/forbid/')
def production_operation_log_list(request):
    sku = request.GET.get('sku', '')
    operation_type = request.GET.get('operation_type', '')
    _form_data = {}
    rm = response_message()
    try:
        page = request.GET.get('page', 1)
        currentPage = int(page)

        ots = inventory_operation_log.objects.filter(operation_type=operation_type).order_by('-created_at')
        if sku:
            ots = inventory_operation_log.objects.filter(operation_type=operation_type, sku=sku)

        items = ots
        _form_data['list'] = items
        _form_data['total'] = ots.count

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
        logging.debug(e.message)
        rm.message(e)
        # json_body = dh.convert_to_dict(rm)
        # json_body = json.dumps(json_body, cls=DateEncoder)
        # return HttpResponse(json_body)

    return render(
        request, "production_operation_log_list.html",
        {
            "form": _form_data,
            'list': items,
            'sku': sku,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': reverse('production_operation_log_list'),
            'query_string': query_string,
        }
    )


@csrf_exempt
@login_required
@permission_required('merchandising.REFRESH_PRODUCT_INDEX', login_url='/oms/forbid/')
def redirect_products_list_csv(request):
    # 查询
    try:
        _form_data = {}
        items = []
        _form_data['items'] = items
        category_id = request.GET.get('category', 6)
        frame = request.GET.get('frame', '')
        min_qty = request.GET.get('min_qty', '')
        max_qty = request.GET.get('max_qty', '')
        cate_type = request.GET.get('cate_type', '')
        if category_id == '':
            category_id = 6

        rm = response_message()

        _form_data["request_module"] = "Merchandising"
        _form_data["request_feature"] = "Web 产品清单"

        from .models import ProductListController
        plc = ProductListController()
        rm = plc.GetAll(category_id, frame, min_qty, max_qty, cate_type)
        items = rm.obj
        response = HttpResponse(content_type='text/csv')
        file_name = 'products_list'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        writer.writerow(['产品清单CSV'])
        writer.writerow(['Img Url', 'Request Url', 'Name', 'Product ID', 'SKU', 'Frame SKU', 'Price', 'Shape', 'Material', 'Bridge',
                         'Temple Length', 'Width', 'Weight', 'Category Name', 'Position', 'Quantity', 'Stock Status'])
        base_url = plc.base_url
        product_url = plc.product_url
        for item in items:
            if item.image_url != '':
                img_url = base_url + item.image_url
            else:
                img_url = ''
            if item.request_path != '':
                request_url = product_url + item.request_path
            else:
                request_url = ''

            writer.writerow([img_url, request_url, item.name, item.product_id, item.sku, item.frame_sku, item.price, item.shape, item.material, item.bridge,
                             item.temple_length, item.width, item.weight, item.category_name, item.position, item.quantity, item.is_in_stock])
        return response
    except Exception as e:
        return HttpResponse(e.message)