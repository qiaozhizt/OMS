# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.db import transaction
from django.http import HttpResponse, JsonResponse
import re

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
from oms.models.order_models import PgOrder, PgOrderItem
from util.db_helper import *
from util.response import *
from util.dict_helper import *


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


def RaNew(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'New RA'
    _response_message = {}
    _response_message['code'] = 0
    _response_message['message'] = 'message'
    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    email = request.GET.get('email', '')
    frame = request.GET.get('frame', '')
    state = request.GET.get('state', '')
    city = request.GET.get('city', '')

    sql = """
        SELECT
            t0.id,
            t0.order_number,
            t0.create_at AS created_at,
            t0.customer_name,
            t0.email,
            t0.total_qty_ordered,
            t0.region AS state,
            t0.city,
            t0.street,
            t0.subtotal,
            t0.shipping_and_handling,
            t0.grand_total,
            t0.total_paid,
            t0.warranty
        FROM
            oms_pgorder t0
        LEFT JOIN oms_pgorderitem t1 ON t1.order_number = t0.order_number
        WHERE 1=1
    """
    sql_condition = ""
    sql_order = """
        group by t0.order_number
        ORDER BY t0.id DESC
        LIMIT 100;
    """
    if order_number:
        sql_condition += " and t0.order_number like '%" + order_number + "'"
    if customer_name:
        sql_condition += " and t0.customer_name like '%" + customer_name + "%'"
    if email:
        sql_condition += " and t0.email like '%" + email + "%'"
    if frame:
        sql_condition += " and t1.frame like '%" + frame + "%'"
    if state:
        sql_condition += " and t1.state like '%" + state + "%'"
    if city:
        sql_condition += " and t1.city like '%" + city + "%'"

    sql = sql + sql_condition + sql_order
    logging.debug(sql)
    results = None

    if sql_condition:
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)

    _order_items = []
    if results:
        _order_items = results

    return render(request, "ra_new.html",
                  {
                      'form_data': _form_data,
                      'order_items': _order_items,
                      'req': request.GET,
                      'response_message': _response_message,
                  })


def RaEdit(request):
    rm = response_message()
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'New RA'
    _response_message = {}
    _response_message['code'] = 0
    _response_message['message'] = 'message'
    order_entity = request.GET.get('order_entity', '')

    pgo = None
    _items = []
    try:
        pgo = PgOrder.objects.get(id=order_entity)
        _items = pgo.get_items
        _order_number_right = pgo.order_number[-5:]
    except Exception as ex:
        logging.critical(str(ex))

    if request.method == 'POST':
        form_data = request.POST.get('form_data', None)
        _items = request.POST.get('items', [])

        form_data = json.loads(form_data)
        _items = json.loads(_items)
        logging.debug(form_data)
        logging.debug(_items)

        dict_data = {}
        oe = form_data['txt_order_entity']
        pgo = PgOrder.objects.get(id=oe)
        _order_number_right = pgo.order_number[-5:]
        dict_data['ra_type'] = form_data['txt_ra_type_key']
        dict_data['order_number_part'] = form_data['txt_order_number']
        dict_data['ticket_id_part'] = form_data['txt_ticket_number']
        label_id = form_data['txt_label_id']
        dict_data['label_id'] = label_id.replace('+', ' ')
        dict_data['amount'] = form_data['txt_amount']

        dict_data['quantity'] = len(_items)
        dict_data['base_entity'] = pgo.id
        dict_data['customer_name'] = pgo.customer_name
        dict_data['order_number'] = pgo.order_number

        # items
        items = []
        for item in _items:
            pgi = pgo.get_item(item)
            items.append(pgi.__dict__)

            # logging.debug(pgi.__dict__)
            # logging.debug(pgi.frame)

        dict_data['items'] = items

        rac = RaController()
        rm = rac.add(request, dict_data)
        logging.debug('----------------------------------------------------------------------')
        logging.debug('-----------------------Response body----------------------------------')
        logging.debug('----------------------------------------------------------------------')
        logging.debug(rm.code)
        logging.debug(rm.message)
        logging.debug('----------------------------------------------------------------------')
        rm = dict_helper.convert_to_dict(rm)

        return HttpResponse(json.dumps(rm))

    return render(request, "ra_new_edit.html",
                  {
                      'form_data': _form_data,
                      'obj': pgo,
                      'order_number_right': _order_number_right,
                      'items': _items,
                      'req': request.GET,
                      'response_message': _response_message,
                  })


def GetList(request, _form_data):
    _response_message = {}
    _response_message['code'] = 0
    _response_message['message'] = 'message'

    page = request.GET.get('page',1)

    order_number = _form_data['params'].get('order_number', '')
    customer_name = _form_data['params'].get('customer_name', '')
    state = _form_data['params'].get('state', '')
    status = _form_data['params'].get('status', '')
    ra_type = _form_data['params'].get('ra_type', '')
    sql_condition_ext = _form_data['params'].get('sql_condition_ext', '')

    logging.debug(_form_data['params'])

    oc = options_choice()
    states = oc.tuple2dict(RaEntity.STATE_CHOICES)
    _form_data['states'] = states

    statuses = oc.tuple2dict(RaEntity.STATUS_CHOICES)
    _form_data['statuses'] = statuses

    logging.debug('req state:[%s]' % request.GET.get('state'))

    sql = """
            SELECT
            t0.id,
            (
            CASE
            WHEN t0.state = '0' THEN
                'Open'
            WHEN t0.state = '10' THEN
                'Processing'
            WHEN t0.state = '90' THEN
                'Completed'
            WHEN t0.state = '901' THEN
                'Closed'
            WHEN t0.state = '902' THEN
                'Canceled'
            ELSE
                ''
            END
            ) AS state,
            (
            CASE
            WHEN t0.STATUS = '0' THEN
                'Created'
            WHEN t0.STATUS = '10' THEN
                'Staging'
            WHEN t0.STATUS = '20' THEN
                'Label'
            WHEN t0.STATUS = '30' THEN
                'Stock In'
            WHEN t0.STATUS = '40' THEN
                'Refund'
            ELSE
                ''
            END
            ) AS status,
            t0.ra_type,
            t0.label_id,
            t0.order_number,
            t0.customer_name,
            t0.quantity,
            t0.amount,
            t0.user_name,
            t0.tracking_code,
            t0.transaction_id,
            t0.created_at,
            t0.updated_at,
            t0.comments
            FROM
            ra_entity t0
            WHERE 1=1       
        """
    sql_condition = ""
    sql_order = """
            ORDER BY
            t0.updated_at DESC
        """
    if order_number:
        sql_condition += " and t0.order_number like '%" + order_number + "'"
    if customer_name:
        sql_condition += " and t0.customer_name like '%" + customer_name + "%'"
    if state:
        sql_condition += " and t0.state= '" + state + "'"
    if status:
        sql_condition += " and t0.status= '" + status + "'"
    if ra_type:
        sql_condition += " and t0.ra_type= '" + ra_type + "'"

    sql = sql + sql_condition + sql_condition_ext + sql_order
    # logging.debug(sql)
    results = None

    with connections['pg_oms_query'].cursor() as cursor:
        cursor.execute(sql)
        results = namedtuplefetchall(cursor)

    _items = []

    if results:
        _items = results
        _form_data['total'] = len(_items)

    paginator = Paginator(_items, 20)  # Show 20 contacts per page

    # 获取URL中除page外的其它参数
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

    logging.debug('----------------------------------------------------------------------')

    return render(request, "ra_list.html",
                  {
                      'form_data': _form_data,
                      'items': _items,
                      'list': _items,
                      'req': request.GET,
                      'response_message': _response_message,
                      'curUrl': request.get_full_path(),
                      'paginator': paginator,
                      'requestUrl': reverse('ra_list'),
                      'query_string': query_string,
                  })


def RaList(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA List'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = state
    params['status'] = status
    params['ra_type'] = ra_type

    _form_data['params'] = params

    actions = []
    action = {}
    action['id'] = 'btnApprove'
    action['value'] = 'Approve'
    actions.append(action)

    action = {}
    action['id'] = 'btnBuyLabel'
    action['value'] = 'Buy Label'
    actions.append(action)

    action = {}
    action['id'] = 'btnStockIn'
    action['value'] = 'Stock In'
    actions.append(action)

    action = {}
    action['id'] = 'btnRefund'
    action['value'] = 'Refund'
    action['class'] = 'btn btn-danger'
    actions.append(action)

    action = {}
    action['id'] = 'btnCoupon'
    action['value'] = 'Coupon'
    action['class'] = 'btn btn-danger'
    actions.append(action)

    # action = {}
    # action['id'] = 'btnClose'
    # action['value'] = 'RA Close'
    # action['class'] = 'btn btn-warning'
    # actions.append(action)
    #
    # action = {}
    # action['id'] = 'btnCancel'
    # action['value'] = 'RA Cancel'
    # action['class'] = 'btn btn-warning'
    # actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def ApproveList(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Approve'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '0'
    params['status'] = status
    params['ra_type'] = ra_type

    _form_data['params'] = params

    actions = []

    action = {}
    action['id'] = 'btnApprove'
    action['value'] = 'Approve'
    actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def BuyLabel(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'Buy RA Label'
    _form_data['action'] = 'BUY_LABEL'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '10'
    params['status'] = '10'
    params['ra_type'] = ra_type

    sql_condition_ext = " and is_label=False "
    params['sql_condition_ext'] = sql_condition_ext

    _form_data['params'] = params

    actions = []
    action = {}
    action['id'] = 'btnBuyLabel'
    action['value'] = 'Buy Label'
    actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def StockIn(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Stock In'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '10'
    params['status'] = status
    params['ra_type'] = ra_type

    sql_condition_ext = " and status in ('10','20') and is_stock=False "
    params['sql_condition_ext'] = sql_condition_ext

    _form_data['params'] = params

    actions = []

    action = {}
    action['id'] = 'btnStockIn'
    action['value'] = 'Stock In'
    actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def Refund(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Refund'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '10'
    params['status'] = status
    params['ra_type'] = ra_type

    sql_condition_ext = " and status in ('10','20','30') and is_refund=False and ra_type<>'CPN'"
    params['sql_condition_ext'] = sql_condition_ext

    _form_data['params'] = params

    actions = []

    action = {}
    action['id'] = 'btnRefund'
    action['value'] = 'Refund'
    action['class'] = 'btn btn-danger'
    actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def Coupon(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Coupon'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '10'
    params['status'] = status
    params['ra_type'] = ra_type

    sql_condition_ext = " and status in ('10','20','30') and is_refund=False and ra_type='CPN' "
    params['sql_condition_ext'] = sql_condition_ext

    _form_data['params'] = params

    actions = []

    action = {}
    action['id'] = 'btnCoupon'
    action['value'] = 'Coupon'
    action['class'] = 'btn btn-danger'
    actions.append(action)

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def Close(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Close'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '10'
    params['status'] = status
    params['ra_type'] = ra_type

    _form_data['params'] = params

    actions = []

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def Cancel(request):
    _form_data = {}
    _form_data['model'] = 'RA Mgmt'
    _form_data['function'] = 'RA Cancel'

    order_number = request.GET.get('order_number', '')
    customer_name = request.GET.get('customer_name', '')
    state = request.GET.get('state', '')
    status = request.GET.get('status', '')
    ra_type = request.GET.get('ra_type', '')

    logging.debug(request.GET)

    params = {}
    params['order_number'] = order_number
    params['customer_name'] = customer_name
    params['state'] = '0'
    params['status'] = status
    params['ra_type'] = ra_type

    _form_data['params'] = params

    actions = []

    _form_data['actions'] = actions

    obj = GetList(request, _form_data)
    return obj


def Action(request):
    rm = response_message()
    form_data = request.POST.get('form_data', None)
    logging.debug(form_data)
    form_data = json.loads(form_data)
    action = form_data.get('action', '')
    email = form_data.get('email', '')
    tracking_code = form_data.get('tracking_code', '')
    location = form_data.get('location', '')
    transaction_id = form_data.get('transaction_id', '')
    comments = form_data.get('comments', '')
    obj = form_data.get('entity', None)

    data = {}
    data['action'] = action
    data['email'] = email
    data['tracking_code'] = tracking_code
    data['location'] = location
    data['transaction_id'] = transaction_id

    data['comments'] = comments
    data['entity'] = obj

    rc = RaController()
    rm = rc.action(request, data)
    logging.debug(rm.code)
    rm_dict = dict_helper.convert_to_dict(rm)
    return HttpResponse(json.dumps(rm_dict))
