# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import time
import json
import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, JsonResponse
from .models import AccsOrder, AccsOrderTracking, AccsOrderRequestNotes, AccsOrderRequestNotesLine, AccsOrderDeliveryLine
from oms.models.order_models import LabOrder,PgOrder,PgOrderItem
from wms.models import warehouse, inventory_struct_warehouse, inventory_struct, inventory_delivery_control
from oms.models.response_models import ParentItems, Items
from util.response import json_response, json_response_page
from .controller import get_by_entity, get_by_entity_filter
from pg_oms import settings
from oms.models.utilities_models import utilities, DateEncoder

# Create your views here.

def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
#@permission_required('stockorder.STOCKORDER_NEW', login_url='/oms/forbid/')
def redirect_accs_order_list_data(request):
    data_list = []
    filter = {}
    try:
        flag = request.GET.get('flag', 'list')
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        accs_order_number = request.GET.get('accs_order_number', '')
        frame_sku = request.GET.get('frame', '')
        order_status = request.GET.get('order_status', '')
        order_wh = request.GET.get('order_wh', '')
        order_delivery = request.GET.get('order_delivery', '')
        order_rx_have = request.GET.get('order_rx_have', '')
        start_date = request.GET.get('start_date', '')
        finish_date = request.GET.get('finish_date', '')

        if accs_order_number:
            filter = get_by_entity_filter(accs_order_number)
        if frame_sku:
            filter['sku'] = frame_sku
        if order_status:
            filter['status'] = order_status
        if order_wh:
            filter['warehouse'] = order_wh
        if order_delivery:
            filter['ship_direction'] = order_delivery

        if order_rx_have:
            if order_rx_have == 'YES':
                filter['is_rx_have'] = True
            else:
                filter['is_rx_have'] = False

        page = int(page)
        start = (page-1) * int(limit)
        end = page * int(limit)
        #判断状态
        if flag == 'list':
            accs_orders = AccsOrder.objects.filter().order_by("-id")
        elif flag == 'assign':
            accs_orders = AccsOrder.objects.filter(status='Open').order_by("-id")
        elif flag == 'print':
            accs_orders = AccsOrder.objects.filter(status__in=('Assigned', 'RePick')).order_by("-id")
        elif flag == 'pick':
            accs_orders = AccsOrder.objects.filter(status='Picking').order_by("-id")
        elif flag == 'pick_list':
            accs_orders = AccsOrder.objects.filter(status__in=('Picking', 'Picked')).order_by("-id")
        elif flag == 'qc':
            accs_orders = AccsOrder.objects.filter(status='Picked').order_by("-id")
        elif flag == 'pack':
            accs_orders = AccsOrder.objects.filter(status='QCed').order_by("-id")
        elif flag == 'ship':
            accs_orders = AccsOrder.objects.filter(status='Packed').order_by("-id")
        elif flag == 'cancel':
            accs_orders = AccsOrder.objects.filter(status__in=('Open', 'onHold')).order_by("-id")
        elif flag == 'close':
            accs_orders = AccsOrder.objects.filter(status__in=('Open', 'onHold')).order_by("-id")
        else:
            accs_orders = AccsOrder.objects.filter().order_by("-id")

        if start_date:
            accs_orders = accs_orders.filter(created_at__gte=start_date).order_by("-id")

        if finish_date:
            accs_orders = accs_orders.filter(created_at__lte=finish_date).order_by("-id")

        accs_orders = accs_orders.filter(**filter)
        total = len(accs_orders)
        fsi_list = accs_orders[start: end]

        for item in fsi_list:
            data_list.append({
                "id": item.id,
                "accs_order_number": item.accs_order_number,
                "order_number": item.order_number,
                "frame_sku": item.sku,
                "name": item.name if item.name else '',
                "image": 'https://static.payneglasses.com/media/catalog/product'+item.image if item.image else '',
                "quantity": item.quantity,
                "repick_quantity": item.repick_quantity,
                "status": item.status,
                "warehouse": item.get_warehouse_display(),
                "is_rx_have": 'YES' if item.is_rx_have else 'NO',
                "order_date":  (item.order_date + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                "shipping_date": (item.ship_date + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if item.ship_date else '',
                "comments": item.comments if item.comments else '',
                "ship_direction": item.get_ship_direction_display(),
                "created_at": (item.created_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if item.created_at else '',
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_LIST', login_url='/oms/forbid/')
def redirect_accs_order_list(request):
    status_data = []
    try:
        title = "Accs Order List"
        flag = request.GET.get('flag', 'list')
        if flag == 'list':
            title = "nRX订单列表"
        elif flag == 'assign':
            title = "nRX订单分配"
        elif flag == 'print':
            title = "nRX订单出库请求"
        elif flag == 'pick':
            title = "nRX订单出库"
        elif flag == 'pick_list':
            title = "nRX订单出库列表"
        elif flag == 'qc':
            title = "nRX订单质检"
        elif flag == 'pack':
            title = "nRX订单包装"
        elif flag == 'pack_list':
            title = "Accs Order Pack List"
        elif flag == 'ship':
            title = "nRX订单发货"
        elif flag == 'cancel':
            title = "nRX订单取消"
        elif flag == 'close':
            title = "nRX订单关闭"

        for item in AccsOrder.STATUS_CHOICES:
            status_data.append(item[0])

        warehouses = warehouse.objects.filter(used_to__in=['ACCESSORIES', 'FRAME'])
        ship_direction_list = []
        SHIP_DIRECTION = AccsOrder.SHIP_DIRECTION_CHOICES
        for item in SHIP_DIRECTION:
            ship_direction_list.append({"key":item[0], "value":item[1]})

        return render(request, "accsorder_list.html", {
            "status_data":status_data,
            "flag":flag,
            "title": title,
            "warehouses": warehouses,
            "ship_direction_list":ship_direction_list

        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_LIST', login_url='/oms/forbid/')
def redirect_change_accs_order_status(request):
    try:
        flag = request.POST.get('flag', '')
        action = request.POST.get('action', '')
        comments = request.POST.get('comments', '')
        checkdata = request.POST.get('checkdata', '')
        checkdata_list = eval(checkdata)
        now_date = datetime.datetime.now()
        data_list = []
        data_accs_list = []
        acc_order_tracking = AccsOrderTracking()

        for item in checkdata_list:
            if action == 'accs_assign':
                if item['status'] == 'Open':
                    AccsOrder.objects.filter(id=item['id']).update(status='Assigned', assign_date=now_date)
                else:
                    return json_response(code=-1, msg='只有【OPen】状态可以进行Assigned')
            elif action == 'accs_print':
                if item['status'] == 'Assigned' or item['status'] == 'RePick':
                    accsorder = AccsOrder.objects.get(id=item['id'])
                    accsorder.status = 'Picking'
                    accsorder.pick_date = now_date
                    accsorder.save()
                    accs_order_request_notes = AccsOrderRequestNotes.objects.filter(last_flag=False, warehouse=accsorder.warehouse)
                    if len(accs_order_request_notes) > 0:
                        accs_order_request_note = accs_order_request_notes[0]
                    else:
                        accs_order_request_note = AccsOrderRequestNotes()
                        accs_order_request_note.count = 0
                        accs_order_request_note.accs_order_number = accsorder.accs_order_number
                        accs_order_request_note.warehouse = accsorder.warehouse
                        accs_order_request_note.save()

                    accorder_requestnote_line = AccsOrderRequestNotesLine()
                    if int(accsorder.repick_quantity) != 0:
                        quantity = accsorder.repick_quantity
                    else:
                        quantity = accsorder.quantity

                    accorder_requestnote_line.add_accsorder_reques_notes_line(accsorder.accs_order_number, accs_order_request_note.id, accsorder.id, accsorder.sku, quantity, accsorder.warehouse, request.user.username)
                else:
                    return json_response(code=-1, msg='只有【Assigned, RePick】状态可以进行Accs PR Print')
            elif action == 'accs_pick':
                if item['status'] == 'Picking':
                    data_dict = {}
                    now = datetime.datetime.now()
                    accorder_requestnote_line = AccsOrderRequestNotesLine.objects.filter(accsorder_id=item['id']).order_by("-base_entity")

                    if len(accorder_requestnote_line) == 0:
                        return json_response(code=-1, msg='AccsOrderRequestNotesLine 为空')

                    accorder_requestnote = AccsOrderRequestNotes.objects.get(id=accorder_requestnote_line[0].base_entity)
                    if not accorder_requestnote.last_flag:
                        return json_response(code=-1, msg='请先打印出库申请单')

                    accs_order = AccsOrder.objects.get(id=item['id'])#.update(status='Picked', pick_date=now_date)


                    if int(accs_order.repick_quantity) != 0:
                        quantity = accs_order.repick_quantity
                    else:
                        quantity = accs_order.quantity

                    invd_ctrl = inventory_delivery_control()
                    if now.month < 10:
                        month = '0' + str(now.month)
                    else:
                        month = str(now.month)
                    if now.day < 10:
                        day = '0' + str(now.day)
                    else:
                        day = str(now.day)

                    accs_order.status = 'Picked'
                    accs_order.pick_date = now_date
                    accs_order.repick_quantity = 0
                    accs_order.save()

                    data_dict['p_number'] = str(now.year) + month + day
                    data_dict['wh_number'] = accs_order.warehouse
                    data_dict['sku'] = accs_order.sku
                    data_dict['doc_type'] = 'AUTO'
                    data_dict['quantity'] = quantity
                    data_dict['comments'] = accs_order.accs_order_number
                    data_dict['lab_number_input'] = accs_order.accs_order_number
                    data_dict['product_type'] = 1
                    data_dict['wh_channel'] = 'WEBSITE'

                    rm = invd_ctrl.add_new(request, data_dict)
                    if rm.code != 0:
                        return json_response(code=-1, msg=rm.message)

                    accs_order_delivery = AccsOrderDeliveryLine()
                    accs_order_delivery.base_entity = accorder_requestnote_line[0].base_entity
                    accs_order_delivery.sku = accs_order.sku
                    accs_order_delivery.quantity = quantity
                    accs_order_delivery.accs_order_number = accs_order.accs_order_number
                    accs_order_delivery.warehouse = accs_order.warehouse
                    accs_order_delivery.user_name = request.user.username
                    accs_order_delivery.user_id = request.user.id
                    accs_order_delivery.save()
                else:
                    return json_response(code=-1, msg='只有【Picking】状态可以进行Accs Pick')
            elif action == 'accs_pass':
                if item['status'] == 'Picked':
                    AccsOrder.objects.filter(id=item['id']).update(status='QCed', qc_date=now_date, comments=comments)
                else:
                    return json_response(code=-1, msg='只有【Picked】状态可以进行Accs Pass')
            elif action == 'accs_resume':
                if item['status'] == 'onHold':
                    accs_order = AccsOrder.objects.get(id=item['id'])
                    last_status = accs_order.last_status
                    accs_order.status = last_status
                    accs_order.last_status = ''
                    accs_order.save()
                else:
                    return json_response(code=-1, msg='只有【onHold】状态可以进行Accs Resume')
            elif action == 'accs_ship':
                if item['status'] == 'Packed':
                    #if len(labs) > 0:
                    if item['is_rx_have'] == 'YES':
                        labs = LabOrder.objects.filter(order_number=item['order_number'])
                        accsorders = AccsOrder.objects.filter(order_number=item['order_number'])
                        for lab in labs:
                            data_list.append({
                                "lab_number": lab.lab_number,
                                "status": lab.get_status_display(),
                                "accs_id": item['id']
                            })

                        for accsorder in accsorders:
                            data_accs_list.append({
                                "order_number": accsorder.order_number,
                                "accs_order_number": accsorder.accs_order_number,
                                "status": accsorder.status
                            })
                        return json_response(code=1, msg='此订单关联到LabOrder,请确认已找到该Laborder', data={"lab":data_list,"accs":data_accs_list})
                    else:
                        accsorders = AccsOrder.objects.filter(order_number=item['order_number'])
                        for accsorder in accsorders:
                            data_accs_list.append({
                                "order_number": accsorder.order_number,
                                "accs_order_number": accsorder.accs_order_number,
                                "status": accsorder.status
                            })
                        return json_response(code=1, msg='此订单包含多个Accs Order,需要同时发货', data={"lab":data_list,"accs":data_accs_list})
                else:
                    return json_response(code=-1, msg='只有【Packed】状态可以进行Accs Ship')
            acc_order_tracking.add_order_tracking(item['accs_order_number'], request.user.id, request.user.username, action)
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_ship(request):
    try:
        accs_id = request.POST.get("accs_id", "")
        now_date = datetime.datetime.now()
        ship_comments = request.POST.get("comments", "")
        accs_orders = AccsOrder.objects.filter(order_number=accs_id)
        packed_accs_orders = accs_orders.filter(order_number=accs_id, status='Packed')
        if len(accs_orders) != len(packed_accs_orders):
            return json_response(code=-1, msg='订单不能进行Ship')

        #注释掉的废弃
        # warehouse_flag = False
        # data = {}
        # data_list = []
        # parcel_service_qty = 0
        acc_order_tracking = AccsOrderTracking()
        for accs_order in accs_orders:
            comments = accs_order.comments
            accs_order.status = 'Shipped'
            accs_order.ship_date = now_date
            accs_order.comments = str(comments) + '\n' + str(ship_comments)
            accs_order.save()
            acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id, request.user.username,
                                             'accs_ship')
            # parcel_service_qty = parcel_service_qty + int(accs_order.quantity)
            # data_list.append({
            #     "order_number": accs_order.order_number,
            #     "accs_order_number": accs_order.accs_order_number,
            #     "accs_base_entity": accs_order.id,
            #     "parcel_service_qty": accs_order.quantity,
            #     "sku": accs_order.sku
            # })
            #
            # if accs_order.warehouse == 'AC01' and not warehouse_flag:
            #     warehouse_flag = True


        # if warehouse_flag:
        #     pgorder = PgOrder.objects.get(order_number=accs_orders[0].order_number)
        #
        #     data['order_number'] = accs_orders[0].order_number
        #     data['to_address_name'] = pgorder.customer_name
        #     data['to_address_street1'] = pgorder.street
        #     data['to_address_street2'] = pgorder.street2
        #     data['to_address_city'] = pgorder.city
        #     data['to_address_sate'] = pgorder.region
        #     data['to_address_zip'] = pgorder.postcode
        #     data['to_address_country'] = pgorder.country_id
        #     data['to_address_phone'] = pgorder.phone
        #     data['order_entity'] = pgorder.id
        #     data['customer_id'] = pgorder.customer_id
        #     data['shipping_address_id'] = pgorder.shipping_address_id
        #     data['billing_address_id'] = pgorder.billing_address_id
        #     data['accs_order_number'] = accs_orders[0].accs_order_number
        #     # data['accs_base_entity'] = accs_order.id
        #     data['parcel_service_qty'] = parcel_service_qty
        #     # data['sku'] = accs_order.sku
        #
        #     data['user_id'] = request.user.id
        #     data['user_name'] = request.user.username
        #     data['data_list'] = data_list
        #
        #     req_data = json.dumps(data, cls=DateEncoder)
        #     token_header = {'Content-Type': 'application/json'}
        #     url = settings.SHIP_ROOT_URL + "/api/create_shipments/"
        #     res_data = requests.post(url,
        #                              data=req_data,
        #                              headers=token_header,
        #                              timeout=10)
        #     res_json = json.loads(res_data.text)
        #     if res_json['code'] == 200:
        #         return json_response(code=0, msg='Success')
        #     else:
        #         return json_response(code=-1, msg=res_json['message'])

        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_action(request):
    try:
        accs_order_id = request.POST.get("accs_order_id", "")
        restock_comments = request.POST.get("restock_comments", "")
        accs_order_flag = request.POST.get("accs_order_flag", "")
        accs_wh = request.POST.get("accs_wh", "")
        repick_quantity = request.POST.get("repick_quantity", "0")
        accs_order_list = accs_order_id.split(",")
        now_date = datetime.datetime.now()
        acc_order_tracking = AccsOrderTracking()
        if accs_order_flag == 'accs_assign':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    old_warehouse = accs_order.warehouse
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)

                    if accs_order.status != 'Open':
                        return json_response(code=-1, msg='只有【OPen】状态可以进行Assigned')

                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'Assigned'
                    accs_order.assign_date = now_date
                    accs_order.warehouse = accs_wh
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    # accs_order_notes = AccsOrderRequestNotes.objects.filter(last_flag=False)
                    # if len(accs_order_notes) == 0:
                    #     accsorderrequestnotes = AccsOrderRequestNotes()
                    #     accsorderrequestnotes.count = 0
                    #     accsorderrequestnotes.accs_order_number = accs_order.accs_order_number
                    #     accsorderrequestnotes.save()
                    comment_msg = u"The original warehouse is【{0}】，Assigned is【{1}】".format(old_warehouse, accs_wh)
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag, True, comment_msg)
        elif accs_order_flag == 'accs_pass':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)
                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'QCed'
                    accs_order.qc_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_repick':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    accs_req_note = AccsOrderRequestNotesLine.objects.filter(accs_order_number=accs_order.accs_order_number).order_by("-id")
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)

                    if len(accs_req_note) == 0:
                        msg = 'AccsOrderRequestNotesLine 为空'
                        return json_response(code=-1, msg=msg)

                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'RePick'
                    accs_order.repick_quantity = repick_quantity
                    accs_order.qc_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()

                    accs_order_delivery_line = AccsOrderDeliveryLine.objects.get(base_entity=accs_req_note[0].base_entity, accs_order_number=accs_order.accs_order_number)
                    dcomment = accs_order_delivery_line.comments if accs_order_delivery_line.comments else ''
                    accs_order_delivery_line.comments = str(dcomment) + '\n' + str(restock_comments)
                    accs_order_delivery_line.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_hold':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)
                    comment = accs_order.comments if accs_order.comments else ''
                    status = accs_order.status
                    accs_order.last_status = status
                    accs_order.status = 'onHold'
                    accs_order.hold_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_pack':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)
                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'Packed'
                    accs_order.pack_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_cancel':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)
                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'Cancelled'
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_close':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    if accs_order.status in ['Cancelled', 'Closed', 'Shipped']:
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作'
                        return json_response(code=-1, msg=msg)
                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'Closed'
                    accs_order.close_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        elif accs_order_flag == 'accs_reship':
            for item in accs_order_list:
                if item != '':
                    accs_order = AccsOrder.objects.get(id=int(item))
                    accs_req_note = AccsOrderRequestNotesLine.objects.filter(accs_order_number=accs_order.accs_order_number).order_by("-id")
                    if accs_order.status != 'Shipped':
                        msg = '订单当前状态【'+accs_order.status+'】，不允许操作,只允许【Shipped】操作'
                        return json_response(code=-1, msg=msg)

                    if len(accs_req_note) == 0:
                        msg = 'AccsOrderRequestNotesLine 为空'
                        return json_response(code=-1, msg=msg)

                    comment = accs_order.comments if accs_order.comments else ''
                    accs_order.status = 'RePick'
                    accs_order.repick_quantity = repick_quantity
                    accs_order.qc_date = now_date
                    accs_order.comments = str(comment) + '--->' + str(restock_comments)
                    accs_order.save()

                    accs_order_delivery_line = AccsOrderDeliveryLine.objects.get(base_entity=accs_req_note[0].base_entity, accs_order_number=accs_order.accs_order_number)
                    dcomment = accs_order_delivery_line.comments if accs_order_delivery_line.comments else ''
                    accs_order_delivery_line.comments = str(dcomment) + '\n' + str(restock_comments)
                    accs_order_delivery_line.save()
                    acc_order_tracking.add_order_tracking(accs_order.accs_order_number, request.user.id,
                                                         request.user.username, accs_order_flag)
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_request_list(request):
    try:
        flag = request.GET.get('flag', 'list')
        warehouses = warehouse.objects.filter(used_to='ACCESSORIES')
        return render(request, "accsorder_request_list.html", {
            "warehouses":warehouses,
            "flag":flag
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_request_list_data(request):
    data_list = []
    filter = {}
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        accs_order_number = request.GET.get('accs_order_number', '')
        frame_sku = request.GET.get('frame', '')
        order_status = request.GET.get('order_status', '')
        order_wh = request.GET.get('order_wh', '')
        start_date = request.GET.get('start_date', '')
        finish_date = request.GET.get('finish_date', '')

        if accs_order_number:
            filter = get_by_entity_filter(accs_order_number)
        if frame_sku:
            filter['sku'] = frame_sku
        if order_status:
            filter['status'] = order_status

        if order_wh:
            filter['warehouse'] = order_wh

        page = int(page)
        start = (page-1) * int(limit)
        end = page * int(limit)
        accs_orders_request_notes = AccsOrderRequestNotes.objects.filter().order_by("-id")
        if start_date:
            accs_orders_request_notes = accs_orders_request_notes.filter(created_at__gte=start_date).order_by("-id")

        if finish_date:
            accs_orders_request_notes = accs_orders_request_notes.filter(created_at__lte=finish_date).order_by("-id")

        accs_orders_request_notes = accs_orders_request_notes.filter(**filter)
        total = len(accs_orders_request_notes)
        fsi_list = accs_orders_request_notes[start: end]
        for item in fsi_list:
            data_list.append({
                "id": item.id,
                "accs_order_number": item.accs_order_number,
                "count": item.count,
                "warehouse": item.get_warehouse_display(),
                "created_at": (item.created_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_request_line(request):
    try:
        return render(request, "accsorder_request_line_list.html", {
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_request_line_data(request):
    data_list = []
    try:
        id = request.GET.get("id", "")
        accorder_requestnote_lines = AccsOrderRequestNotesLine.objects.filter(base_entity=id).order_by("-id")
        for item in accorder_requestnote_lines:
            loaction = ''
            isws = inventory_struct_warehouse.objects.filter(sku=item.sku,warehouse_code=item.warehouse)
            if len(isws) > 0:
                loaction = isws[0].location
            data_list.append({
                "id": item.id,
                "accs_order_number": item.accs_order_number,
                "sku": item.sku,
                "quantity": item.quantity,
                "warehouse": item.get_warehouse_display(),
                "loaction": loaction,
                "created_at": (item.created_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
            })
        total = len(accorder_requestnote_lines)
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_request_notes_print(request):
    _form_data = {}
    try:
        id = request.GET.get('id', '')
        _form_data['id'] = id
        lines = request.GET.get('lines', 30)
        accorder_requestnote_lines = AccsOrderRequestNotesLine.objects.filter(base_entity=id).order_by("-id")

        items = accorder_requestnote_lines
        count = len(items)  # 数据总条数
        lines = int(lines)  # 每页总行数
        copies = count // lines
        remainder = count % lines
        if remainder > 0:
            copies += 1

        index = 0
        items = []

        for i in range(copies):
            pitms = ParentItems()
            pitms.index = i + 1
            pitms.count = copies
            pitms.created_at = datetime.date.today()
            pitms.warehouse_code = ''
            pitms.items = []

            for j in range(lines):
                itm = Items()
                itm.index = index

                invss = inventory_struct_warehouse.objects.filter(sku=accorder_requestnote_lines[index].sku, warehouse_code=accorder_requestnote_lines[index].warehouse)

                if len(invss) > 0:
                    itm.quantity = invss[0].quantity
                    itm.location = invss[0].location

                obj = Items()
                obj.index = index + 1
                obj.obj = accorder_requestnote_lines[index]
                itm.left = obj
                pitms.items.append(itm)

                index += 1
                if index == count:
                    break

            items.append(pitms)
            if index == count:
                break

        AccsOrderRequestNotes.objects.filter(id=id).update(last_flag=True)

        return render(request, "accsorder_request_notes_print.html", {
            'list': items,
            'form_data': _form_data,

        })
    except Exception as e:
        return render(request, "accsorder_request_notes_print.html", {
            'list': items,
            'form_data': _form_data,
        })

@login_required
def redirect_accs_order_request_notes_generate_barcode(request):
    items = []
    try:
        id = request.GET.get('id', '')

        # Print Start
        lbos = AccsOrderRequestNotesLine.objects.filter(base_entity=id).order_by("-id")

        for lbo in lbos:
            items.append('%s|A%d' % (lbo.accs_order_number, lbo.accsorder_id))
        response = HttpResponse(content_type='text')
        file_name = 'accsorder_numbers_barcode'
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
        return HttpResponse('生成条码标签清单遇到异常[ %s ], 请暂时手动生成，并联系系统支持....' % e.message)


@login_required
def redirect_accs_order_pick_list(request):
    try:
        flag = request.GET.get('flag', 'list')
        warehouses = warehouse.objects.filter(used_to='ACCESSORIES')
        ship_direction_list = []
        SHIP_DIRECTION = AccsOrder.SHIP_DIRECTION_CHOICES
        for item in SHIP_DIRECTION:
            ship_direction_list.append({"key":item[0], "value":item[1]})
        return render(request, "accsorder_delivery_list.html", {
            "warehouses":warehouses,
            "ship_direction_list":ship_direction_list,
            "flag":flag
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_pick_list_data(request):
    data_list = []
    filter = {}
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        accs_order_number = request.GET.get('accs_order_number', '')
        frame_sku = request.GET.get('frame', '')
        order_status = request.GET.get('order_status', '')
        start_date = request.GET.get('start_date', '')
        finish_date = request.GET.get('finish_date', '')

        if accs_order_number:
            filter['accs_order_number'] = accs_order_number
        if frame_sku:
            filter['sku'] = frame_sku
        if order_status:
            filter['status'] = order_status

        page = int(page)
        start = (page-1) * int(limit)
        end = page * int(limit)
        accs_orders_request_notes = AccsOrderDeliveryLine.objects.filter().order_by("-id")
        if start_date:
            accs_orders_request_notes = accs_orders_request_notes.filter(created_at__gte=start_date).order_by("-id")

        if finish_date:
            accs_orders_request_notes = accs_orders_request_notes.filter(created_at__lte=finish_date).order_by("-id")

        accs_orders_request_notes = accs_orders_request_notes.filter(**filter)
        total = len(accs_orders_request_notes)
        fsi_list = accs_orders_request_notes[start: end]
        for item in fsi_list:
            data_list.append({
                "id": item.id,
                "accs_order_number": item.accs_order_number,
                "sku": item.sku,
                "quantity": str(item.quantity),
                "warehouse": item.warehouse,
                "user_name": item.user_name,
                "base_entity": item.base_entity,
                "comments": item.comments,
                "created_at": (item.created_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_order_pick(request):
    try:
        data_dict = {}
        accs_order_number = request.POST.get('accs_order_number', '')
        now = datetime.datetime.now()
        accs_orders = get_by_entity(accs_order_number)
        for accs_order in accs_orders:
            if accs_order.status != 'Picking':
                return json_response(code=-1, msg='只有【Picking】状态可以进行Accs Pick')

            accorder_requestnote_line = AccsOrderRequestNotesLine.objects.filter(accsorder_id=accs_order.id).order_by(
                "-base_entity")
            accorder_requestnote = AccsOrderRequestNotes.objects.get(id=accorder_requestnote_line[0].base_entity)
            if not accorder_requestnote.last_flag:
                return json_response(code=-1, msg='请先打印出库申请单')
            invd_ctrl = inventory_delivery_control()
            if now.month < 10:
                month = '0' + str(now.month)
            else:
                month = str(now.month)
            if now.day < 10:
                day = '0' + str(now.day)
            else:
                day = str(now.day)

            accs_order.status = 'Picked'
            accs_order.pick_date = now
            accs_order.save()

            data_dict['p_number'] = str(now.year) + month + day
            data_dict['wh_number'] = accs_order.warehouse
            data_dict['sku'] = accs_order.sku
            data_dict['doc_type'] = 'AUTO'
            data_dict['quantity'] = accs_order.quantity
            data_dict['comments'] = accs_order.accs_order_number
            data_dict['lab_number_input'] = accs_order.accs_order_number
            data_dict['product_type'] = 1
            data_dict['wh_channel'] = 'WEBSITE'

            rm = invd_ctrl.add_new(request, data_dict)
            if rm.code != 0:
                return json_response(code=-1, msg=rm.message)

            accs_order_delivery = AccsOrderDeliveryLine()
            accs_order_delivery.base_entity = accorder_requestnote_line[0].base_entity
            accs_order_delivery.sku = accs_order.sku
            accs_order_delivery.quantity = accs_order.quantity
            accs_order_delivery.accs_order_number = accs_order.accs_order_number
            accs_order_delivery.warehouse = accs_order.warehouse
            accs_order_delivery.user_name = request.user.username
            accs_order_delivery.user_id = request.user.id
            accs_order_delivery.save()

        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_accs_to_lab(request):
    try:
        checkdata = request.POST.get('checkdata', '')
        acc_order_tracking = AccsOrderTracking()
        checkdata_list = eval(checkdata)
        item = checkdata_list[0]
        if item['status'] == 'Open':
            pgorderitems = PgOrderItem.objects.filter(frame__contains=item['frame_sku'], order_number=item['order_number'],lab_order_number='')
            if len(pgorderitems) > 0:
                pgorderitem = pgorderitems[0]
                try:
                    for i in range(0, pgorderitem.quantity):
                        lbo = pgorderitem.generate_lab_order(index=i, flag='accs')
                except Exception as e:
                    return json_response(code=-1, msg='转lab失败')
                if lbo:
                    AccsOrder.objects.filter(accs_order_number=item['accs_order_number']).update(status='Closed', comments='此订单转Laborder')
                    acc_order_tracking.add_order_tracking(item['accs_order_number'], request.user.id,request.user.username, 'accs_to_lab')
                    return json_response(code=0, msg='Success')
                else:
                    return json_response(code=-1, msg='转lab失败')
            else:
                return json_response(code=-1, msg='PgOrderItem不存在')
        else:
            return json_response(code=-1, msg='只有Open状态允许转Lab')
    except Exception as e:
        return json_response(code=-1, msg=e)