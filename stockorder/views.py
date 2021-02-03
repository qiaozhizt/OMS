# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from .models import StockOrder, StockInRequest, StockStruct, InterbranchOrder, StockStructLine,StockBomStruct
from .controller import stockorder_to_laborder_controller
from oms.models.order_models import LabOrder
from wms.models import warehouse, product_lens,product_frame,inventory_struct,inventory_struct_warehouse,inventory_receipt_control,inventory_delivery,inventory_receipt
from util.response import json_response, json_response_page
from django.db import connections
from oms.views import namedtuplefetchall, status_choice

# Create your views here.

def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('stockorder.STOCKORDER_NEW', login_url='/oms/forbid/')
def redirect_stock_order_new(request):
    try:
        t = time.time()
        now_time = int(round(t * 1000))
        stock_order_number = "STKO" + str(now_time)
        product_frame_lists = product_frame.objects.filter(product_type='STKG')
        return render(request, "stockorder_new.html", {
            "stock_order_number": stock_order_number,
            "product_frame_lists": product_frame_lists
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_NEW', login_url='/oms/forbid/')
def redirect_stock_order_new_data(request):
    data_list = []
    filter = {}
    try:
        flag = request.GET.get('flag', 'list')
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        stock_order_number = request.GET.get('stock_order_number', '')
        frame_sku = request.GET.get('frame_sku', '')
        order_status = request.GET.get('order_status', '')
        start_date = request.GET.get('start_date', '')
        finish_date = request.GET.get('finish_date', '')

        if stock_order_number:
            filter['stock_order_number'] = stock_order_number
        if frame_sku:
            filter['frame'] = frame_sku
        if order_status:
            filter['status'] = order_status

        page = int(page)
        start = (page-1) * int(limit)
        end = page * int(limit)
        sql ="""SELECT t0.id as stock_id, t0.stock_order_number,t0.frame as product_sku,t0.quantity,t0.remaining_qty,t0.status,
                       CONVERT_TZ(t0.start_date, @@session.time_zone,'+8:00') as start_date,
                       CONVERT_TZ(t0.finish_date, @@session.time_zone,'+8:00') as finish_date,
                       t0.comments,t0.user_name,t1.od_lens_name,t1.od_lens_sku,t1.od_sph,t1.od_cyl,
                       t1.os_lens_name,t1.os_lens_sku,t1.os_sph,t1.os_cyl, t1.frame 
                FROM stock_order AS t0 
                    LEFT JOIN stock_bom_struct AS t1 
                    ON t0.frame=t1.product_sku 
                WHERE t1.id<>'' """

        count_sql ="""SELECT count(t0.id) as cnt FROM stock_order AS t0 LEFT JOIN stock_bom_struct AS t1 ON t0.frame=t1.product_sku WHERE t1.id<>'' """

        if stock_order_number:
            count_sql = count_sql + """AND t0.stock_order_number='%s' """ % stock_order_number
            sql = sql + """AND t0.stock_order_number='%s' """ % stock_order_number
        if frame_sku:
            count_sql = count_sql + """AND t0.frame='%s' """ % frame_sku
            sql = sql + """AND t0.frame='%s' """ % frame_sku
        if order_status:
            count_sql = count_sql + """AND t0.status='%s' """ % order_status
            sql = sql + """AND t0.status='%s' """ % order_status

        if start_date:
            count_sql = count_sql + """AND CONVERT_TZ(t0.start_date, @@session.time_zone,'+8:00')>='%s' """ % start_date
            sql = sql + """AND CONVERT_TZ(t0.start_date, @@session.time_zone,'+8:00')>='%s' """ % start_date

        if finish_date:
            count_sql = count_sql + """AND CONVERT_TZ(t0.finish_date, @@session.time_zone,'+8:00')<='%s' """ % finish_date
            sql = sql + """AND CONVERT_TZ(t0.finish_date, @@session.time_zone,'+8:00')<='%s' """ % finish_date

        with connections['pg_oms_query'].cursor() as cursor:
            if flag == 'list':
                count_sql = count_sql + """ ORDER BY t0.id DESC"""
                sql = sql + """ ORDER BY t0.id DESC LIMIT %s, %s """ %(start, end)
            elif flag == 'cancel' or flag == 'confirm':
                count_sql = count_sql + """ and status='Open' ORDER BY t0.id DESC"""
                sql = sql + """ and status='Open' ORDER BY t0.id DESC LIMIT %s, %s """ % (start, end)
            elif flag == 'close':
                count_sql = count_sql + """ and status in ('Open', 'Processing') ORDER BY t0.id DESC"""
                sql = sql + """ and status in ('Open', 'Processing') ORDER BY t0.id DESC LIMIT %s, %s """ % (start, end)
            elif flag == 'create':
                count_sql = count_sql + """ and status in ('Confirm', 'Processing') ORDER BY t0.id DESC"""
                sql = sql + """ and status in ('Confirm', 'Processing') ORDER BY t0.id DESC LIMIT %s, %s """ % (start, end)
            else:
                count_sql = count_sql + """ ORDER BY t0.id DESC"""
                sql = sql + """ ORDER BY t0.id DESC LIMIT %s, %s """ % (start, end)

            cursor.execute(sql)
            fsi_list = namedtuplefetchall(cursor)
            cursor.execute(count_sql)
            fsi_counts = namedtuplefetchall(cursor)
        # #判断状态
        # if flag == 'list':
        #     stock_orders = StockOrder.objects.filter().order_by("-id")
        # elif flag == 'cancel' or flag == 'confirm':
        #     stock_orders = StockOrder.objects.filter(status='Open').order_by("-id")
        # elif flag == 'close':
        #     stock_orders = StockOrder.objects.filter(status__in=('Open', 'Processing')).order_by("-id")
        # elif flag == 'create':
        #     stock_orders = StockOrder.objects.filter(status__in=('Confirm', 'Processing')).order_by("-id")
        # else:
        #     stock_orders = StockOrder.objects.filter().order_by("-id")
        #
        # if start_date:
        #     stock_orders = stock_orders.filter(start_date__gte=start_date).order_by("-id")
        #
        # if finish_date:
        #     stock_orders = stock_orders.filter(finish_date__lte=finish_date).order_by("-id")
        #
        # stock_orders = stock_orders.filter(**filter)
        # total = len(stock_orders)
        # fsi_list = stock_orders[start: end]
        total = fsi_counts[0].cnt
        for item in fsi_list:
            data_list.append({
                "id": item.stock_id,
                "stock_order_number": item.stock_order_number,
                "product_sku": item.product_sku,
                "quantity": item.quantity,
                "remaining_qty": item.remaining_qty,
                "status": item.status,
                "start_date": item.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "finish_date": item.finish_date.strftime("%Y-%m-%d %H:%M:%S"),
                "comments": item.comments,
                "user_name": item.user_name,
                "lab_qty": 0,
                "frame": item.frame,
                "od_lens_sku": item.od_lens_sku,
                "od_lens_name": item.od_lens_name,
                "od_lens_sph": str(item.od_sph),
                "od_lens_cyl": str(item.od_cyl),
                "od_len_qty": str(item.quantity),
                "os_lens_sku": item.os_lens_sku,
                "os_lens_name": item.os_lens_name,
                "os_lens_sph": str(item.os_sph),
                "os_lens_cyl": str(item.os_cyl),
                "os_len_qty": str(item.quantity)
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_NEW', login_url='/oms/forbid/')
def redirect_stock_order_save(request):
    try:
        stock_order_number = request.POST.get('stock_order_number', '')
        start_date = request.POST.get('start_date', '')
        finish_date = request.POST.get('finish_date', '')
        frame_sku = request.POST.get('frame_sku', '')
        lens_sku = request.POST.get('lens_sku', '')
        quantity = request.POST.get('quantity', '')
        comments = request.POST.get('comments', '')

        stock_orders = StockOrder.objects.filter(stock_order_number=stock_order_number)
        if len(stock_orders) > 0:
            return json_response(code=-1, msg='该订单已存在！', data='')

        stockbomstruct_list = StockBomStruct.objects.filter(product_sku=frame_sku.upper())
        if len(stockbomstruct_list) == 0:
            return json_response(code=-1, msg='请先在BOM创建该成镜SKU！', data='')

        new_stock_order = StockOrder()
        new_stock_order.stock_order_number = stock_order_number
        new_stock_order.start_date = start_date
        new_stock_order.finish_date = finish_date
        new_stock_order.frame = frame_sku.upper()
        new_stock_order.lens_sku = lens_sku.upper()
        new_stock_order.quantity = quantity
        new_stock_order.remaining_qty = quantity
        new_stock_order.comments = comments
        new_stock_order.user_name = request.user.username
        new_stock_order.user_id = request.user.id
        new_stock_order.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        print(e)
        print('1111111111111111111')
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_LIST', login_url='/oms/forbid/')
def redirect_stock_order_list(request):
    status_data = []
    try:
        title = "成镜订单列表"
        flag = request.GET.get('flag', 'list')
        if flag == 'list':
            title = "成镜订单列表"
        elif flag == 'confirm':
            title = "成镜订单确认"
        elif flag == 'cancel':
            title = "成镜订单取消"
        elif flag == 'close':
            title = "成镜订单关闭"
        elif flag == 'create':
            title = "从成镜订单生成Lab Order"

        for item in StockOrder.STATUS_CHOICES:
            status_data.append(item[0])
        return render(request, "stockorder_list.html", {
            "status_data":status_data,
            "flag":flag,
            "title": title
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_LIST', login_url='/oms/forbid/')
def redirect_change_stock_order_status(request):
    try:
        flag = request.POST.get('flag', '')
        action = request.POST.get('action', '')
        checkdata = request.POST.get('checkdata', '')
        checkdata_list = eval(checkdata)
        for item in checkdata_list:
            if action == 'cancel':
                if item['status'] == 'Open':
                    StockOrder.objects.filter(id=item['id']).update(status='Cancel', remaining_qty=0)
                else:
                    return json_response(code=-1, msg='只有【Open】状态的StockOrder，才能Cancel')
            elif action == 'close':
                if item['status'] == 'Open' or item['status'] == 'Processing':
                    StockOrder.objects.filter(id=item['id']).update(status='Close')
                else:
                    return json_response(code=-1, msg='只有【Open，Processing】状态的StockOrder，才能Close')
            elif action == 'confirm':
                if item['status'] == 'Open':
                    StockOrder.objects.filter(id=item['id']).update(status='Confirm')
                else:
                    return json_response(code=-1, msg='只有【Open】状态的StockOrder，才能Confirm')
            elif action == 'create':
                if item['status'] == 'Confirm' or item['status'] == 'Processing':
                    stlc = stockorder_to_laborder_controller()
                    data = stlc.create_laborder(item, flag)
                    if data['code'] != 0:
                        return json_response(code=-1, msg='LabOrder 创建失败')
                    else:
                        if flag == 'list':
                            StockOrder.objects.filter(id=item['id']).update(status='Finish', remaining_qty=0)
                        else:
                            diff_qty = int(item['remaining_qty']) - int(item['lab_qty'])
                            if diff_qty > 0:
                                StockOrder.objects.filter(id=item['id']).update(status='Processing', remaining_qty=diff_qty)
                            else:
                                StockOrder.objects.filter(id=item['id']).update(status='Finish', remaining_qty=0)
                else:
                    return json_response(code=-1, msg='只有【Confirm】状态的StockOrder，才能Create LabOrder')
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_create_stock_in_request_list(request):
    try:
        return render(request, "create_stock_in_request_list.html", {
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_get_stko_laborder_data(request):
    data_list = []
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        lab_number = request.GET.get('lab_number', '')
        start_date = request.GET.get('start_date', '')


        page = int(page)
        start = (page - 1) * int(limit)
        end = page * int(limit)

        if lab_number != '':
            if len(lab_number) <= 10 and len(lab_number) >= 4:
                count = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES', lab_number__contains=lab_number).count()
                labs = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES', lab_number__contains=lab_number).order_by('-id')[start: end]
            else:
                count = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES', lab_number=lab_number).count()
                labs = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES', lab_number=lab_number).order_by("-id")[start: end]
        else:
            count = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES').count()
            labs = LabOrder.objects.filter(type='STKO', status='FINAL_INSPECTION_YES').order_by("-id")[start: end]
        total = count#len(labs)
        #fsi_list = labs[start: end]
        for item in labs:
            data_list.append({
                "id": item.id,
                "lab_number": item.lab_number,
                "sku": item.frame,
                "lens_sku": item.act_lens_sku,
                "lens_name": item.act_lens_name,
                "quantity": item.quantity,
                "order_number": item.order_number
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_create_stock_in_request(request):
    try:
        stock_order_number = request.POST.get('stock_order_number', '')
        lab_number = request.POST.get('lab_number', '')
        frame = request.POST.get('frame', '')
        #lens_sku = request.POST.get('lens_sku', '')
        quantity = request.POST.get('quantity', '')
        act_quantity = request.POST.get('act_quantity', '')
        comments = request.POST.get('comments', '')

        if act_quantity == '':
            return json_response(code=-1, msg='参数不能为空')

        stockinrequests = StockInRequest.objects.filter(lab_number=lab_number)
        if len(stockinrequests) > 0:
            return json_response(code=-1, msg='该订单已经生成了StockInRequest')

        stock_order = StockOrder.objects.get(stock_order_number=stock_order_number)
        new_stockin_request = StockInRequest()
        new_stockin_request.lab_number = lab_number
        new_stockin_request.frame = stock_order.frame
        new_stockin_request.stock_order_number = stock_order_number
        new_stockin_request.quantity = quantity
        new_stockin_request.act_quantity = act_quantity
        new_stockin_request.comments = comments
        new_stockin_request.user_id = request.user.id
        new_stockin_request.user_name = request.user.username
        new_stockin_request.save()

        LabOrder.objects.filter(lab_number=lab_number).update(status='PreStockIn')
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_stock_in_request_list(request):
    inbound_type_list = []
    try:
        whs = warehouse.objects.filter()
        for item in StockStruct.TYPE_CHOICES:
            inbound_type_list.append({
                'code': item[0],
                'name': item[1]
            })
        return render(request, "stock_in_request_list.html", {
            "whs": whs,
            "inbound_type_list": inbound_type_list
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_get_stock_in_request_data(request):
    data_list = []
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        lab_number = request.GET.get('lab_number', '')


        page = int(page)
        start = (page - 1) * int(limit)
        end = page * int(limit)
        if lab_number != '':
            count = StockInRequest.objects.filter(status='Open', lab_number=lab_number).count()
            stockinrequests = StockInRequest.objects.filter(status='Open', lab_number=lab_number).order_by("-id")[start: end]
        else:
            count = StockInRequest.objects.filter(status='Open').count()
            stockinrequests = StockInRequest.objects.filter(status='Open').order_by("-id")[start: end]

        total = count
        for item in stockinrequests:
            data_list.append({
                "id": item.id,
                "stock_order_number": item.stock_order_number,
                "lab_number": item.lab_number,
                "frame": item.frame,
                "lens_sku": item.lens_sku,
                "quantity": item.quantity,
                "act_quantity": item.act_quantity,
                "status": item.status

            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_create_stock_in(request):
    try:
        stock_order_number = request.POST.get('stock_order_number', '')
        lab_number = request.POST.get('lab_number', '')
        frame = request.POST.get('frame', '')
        lens_sku = request.POST.get('lens_sku', '')
        inbound_type = request.POST.get('inbound_type', '')
        warehouse_code = request.POST.get('warehouse', '')
        location = request.POST.get('location', '')
        quantity = request.POST.get('quantity', '')
        comments = request.POST.get('comments', '')
        if quantity == '':
            return json_response(code=-1, msg='参数不能为空')

        stockstructlines = StockStructLine.objects.filter(lab_number=lab_number)
        if len(stockstructlines) > 0:
            return json_response(code=-1, msg='该订单已经生成了StockStruct')

        p_number = datetime.datetime.now().strftime('%Y%m%d')
        #增加StockStruct start
        invr_ctrl = inventory_receipt_control()
        rm = invr_ctrl.add(request, p_number, warehouse_code, frame.upper(),
                           0, inbound_type, quantity, comments)
        if rm.code == 0:
            stlrs = LabOrder.objects.filter(lab_number=lab_number)
            stock_order_number = stlrs[0].order_number

            new_stockstructline = StockStructLine()
            new_stockstructline.stock_order_number = stock_order_number
            new_stockstructline.lab_number = lab_number
            new_stockstructline.frame = frame.upper()
            new_stockstructline.lens_sku = lens_sku.upper()
            new_stockstructline.quantity = quantity
            new_stockstructline.warehouse = warehouse_code
            new_stockstructline.location = location
            new_stockstructline.inbound_type = inbound_type
            new_stockstructline.comments = comments
            new_stockstructline.user_id = request.user.id
            new_stockstructline.user_name = request.user.username
            new_stockstructline.save()
            StockInRequest.objects.filter(lab_number=lab_number).update(status='Finish')
            LabOrder.objects.filter(lab_number=lab_number).update(status='DELIVERED')
            return json_response(code=0, msg='Success')
        else:
            return json_response(code=-1, msg=rm.msg)

    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_stock_in_list(request):
    try:
        return render(request, "stock_in_list.html", {
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_stock_in_list_data(request):
    data_list = []
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        lab_number = request.GET.get('lab_number', '')


        page = int(page)
        start = (page - 1) * int(limit)
        end = page * int(limit)
        if lab_number != '':
            count = StockStructLine.objects.filter(lab_number__contains=lab_number).count()
            stockins = StockStructLine.objects.filter(lab_number__contains=lab_number).order_by("-id")[start: end]
        else:
            count = StockStructLine.objects.filter().count()
            stockins = StockStructLine.objects.filter().order_by("-id")[start: end]

        total = count
        for item in stockins:
            data_list.append({
                "id": item.id,
                "stock_order_number": item.stock_order_number,
                "lab_number": item.lab_number,
                "frame": item.frame,
                "lens_sku": item.lens_sku,
                "quantity": item.quantity,
                "warehouse": item.warehouse,
                "location": item.location,
                "username": item.user_name,
                "comments": item.comments

            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_stock_struct_list(request):
    try:
        whs = warehouse.objects.filter()
        return render(request, "stock_struct_list.html", {
            "whs": whs
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_stock_struct_list_data(request):
    data_list = []
    filter = {}
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        frame = request.GET.get('frame', '')
        warehouse = request.GET.get('warehouse', '')
        page = int(page)
        start = (page - 1) * int(limit)
        end = page * int(limit)
        if frame != '' and warehouse != '':
            filter['frame__contains'] = frame
            filter['warehouse'] = warehouse
        elif frame != '':
            filter['frame__contains'] = frame
        elif warehouse != '':
            filter['warehouse'] = warehouse

        count = StockStruct.objects.filter(**filter).count()
        stockins = StockStruct.objects.filter(**filter).order_by("-id")[start: end]

        total = count
        for item in stockins:
            data_list.append({
                "id": item.id,
                "frame": item.frame,
                "lens_sku": item.lens_sku,
                "quantity": item.quantity,
                "warehouse": item.warehouse,
                "location": item.location,
                "comments": item.comments

            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_INTERBRANCH', login_url='/oms/forbid/')
def redirect_interbranch_transfer_new(request):
    try:
        whs = warehouse.objects.filter()
        t = time.time()
        now_time = int(round(t * 1000))
        stock_order_number = "IT" + str(now_time)
        product_frame_lists = product_frame.objects.filter(product_type='STKG')
        return render(request, "interbranch_transfer_new.html", {
            "stock_order_number": stock_order_number,
            "whs": whs,
            "product_frame_lists": product_frame_lists

        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_INTERBRANCH_NEW', login_url='/oms/forbid/')
def redirect_interbranch_order_save(request):
    try:
        interbranch_order_number = request.POST.get('interbranch_order_number', '')
        issuing_warehouse = request.POST.get('issuing_warehouse', '')
        issuing_location = request.POST.get('issuing_location', '')
        receiving_warehouse = request.POST.get('receiving_warehouse', '')
        receiving_location = request.POST.get('receiving_location', '')
        frame_sku = request.POST.get('frame_sku', '')
        lens_sku = request.POST.get('lens_sku', '')
        quantity = request.POST.get('quantity', '')
        sku_attribute = request.POST.get('sku_attribute', '')
        fulfilment_date = request.POST.get('fulfilment_date', '')
        comments = request.POST.get('comments', '')
        interbranch_orders = InterbranchOrder.objects.filter(interbranch_order_number=interbranch_order_number)

        if len(interbranch_orders) > 0:
            return json_response(code=-1, msg='The order number already exists', data='')

        #创建内部移库单 start
        invsws = inventory_struct_warehouse.objects.filter(sku=frame_sku.upper(), warehouse_code=issuing_warehouse)
        if len(invsws) == 0:
            return json_response(code=-1, msg='该仓库不存在SKU库存，请确认')
        invsw = invsws[0]
        diff_quantity = invsw.quantity - int(quantity)
        if diff_quantity < 0:
            return json_response(code=-1, msg='移库数量大于库存数量,不能移库，请确认')

        new_interbranch_order = InterbranchOrder()
        new_interbranch_order.interbranch_order_number = interbranch_order_number
        new_interbranch_order.warehouse_from = issuing_warehouse
        new_interbranch_order.location_from = issuing_location
        new_interbranch_order.warehouse_to = receiving_warehouse
        new_interbranch_order.location_to = receiving_location
        new_interbranch_order.frame = frame_sku.upper()
        new_interbranch_order.lens_sku = lens_sku.upper()
        new_interbranch_order.quantity = quantity
        new_interbranch_order.sku_attribute = sku_attribute
        new_interbranch_order.fulfil_date = fulfilment_date
        new_interbranch_order.comments = comments
        new_interbranch_order.user_name = request.user.username
        new_interbranch_order.user_id = request.user.id
        new_interbranch_order.save()

        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
#@permission_required('stockorder.STOCKORDER_LIST', login_url='/oms/forbid/')
def redirect_interbranch_order_list(request):
    status_data = []
    try:
        whs = warehouse.objects.filter()
        title = "Interbranch Transfer List"
        flag = request.GET.get('flag', 'list')
        if flag == 'list':
            title = "内部调拨单列表"
        elif flag == 'print':
            title = "内部调拨单打印"
        elif flag == 'cancel':
            title = "内部调拨单取消"
        elif flag == 'fulfill':
            title = "内部调拨调出"
        elif flag == 'receive':
            title = "内部调拨接收"

        for item in InterbranchOrder.STATUS_CHOICES:
            status_data.append(item[0])
        return render(request, "interbranchorder_list.html", {
            "status_data": status_data,
            "flag": flag,
            "title": title,
            "whs": whs
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_interbranch_order_list_data(request):
    data_list = []
    filter = {}
    try:
        flag = request.GET.get('flag', '')
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        interbranch_order_number = request.GET.get('interbranch_order_number', '')
        issuing_warehouse = request.GET.get('issuing_warehouse', '')
        receiving_warehouse = request.GET.get('receiving_warehouse', '')
        frame_sku = request.GET.get('frame_sku', '')
        order_status = request.GET.get('order_status', '')
        sku_attribute = request.GET.get('sku_attribute', '')

        if interbranch_order_number != '':
            filter['interbranch_order_number'] = interbranch_order_number
        if issuing_warehouse != '':
            filter['warehouse_from'] = issuing_warehouse
        if receiving_warehouse != '':
            filter['warehouse_to'] = receiving_warehouse
        if frame_sku != '':
            filter['frame'] = frame_sku
        if order_status != '':
            filter['status'] = order_status
        if sku_attribute != '':
            filter['sku_attribute'] = sku_attribute

        page = int(page)
        start = (page - 1) * int(limit)
        end = page * int(limit)
        #判断状态
        if flag == 'list':
            interbranch_orders = InterbranchOrder.objects.filter().order_by("-id")
        elif flag == 'print':
            interbranch_orders = InterbranchOrder.objects.filter(status='Open').order_by("-id")
        elif flag == 'cancel':
            interbranch_orders = InterbranchOrder.objects.filter(status__in=('Open', 'Printed')).order_by("-id")
        elif flag == 'fulfill':
            interbranch_orders = InterbranchOrder.objects.filter(status='Printed').order_by("-id")
        elif flag == 'receive':
            interbranch_orders = InterbranchOrder.objects.filter(status='Fulfilled').order_by("-id")
        else:
            interbranch_orders = InterbranchOrder.objects.filter().order_by("-id")

        if len(filter) > 0:
            count = interbranch_orders.filter(**filter).count()
            interbranch_orders = interbranch_orders.filter(**filter).order_by("-id")[start: end]
        else:
            count = interbranch_orders.filter().count()
            interbranch_orders = interbranch_orders.filter().order_by("-id")[start: end]

        total = count
        for item in interbranch_orders:
            data_list.append({
                "id": item.id,
                "interbranch_order_number": item.interbranch_order_number,
                "frame": item.frame,
                "lens_sku": item.lens_sku,
                "quantity": item.quantity,
                "status": item.status,
                "warehouse_from": item.warehouse_from,
                "warehouse_to": item.warehouse_to,
                "fulfil_date": (item.fulfil_date+datetime.timedelta(hours=+8)).strftime("%Y-%m-%d %H:%M:%S"),
                "comments": item.comments

            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_change_interbranch_order_status(request):
    data_list = []
    try:
        action = request.POST.get('action', '')
        checkdata = request.POST.get('checkdata', '')
        checkdata_list = eval(checkdata)
        for item in checkdata_list:
            if action == 'print':
                if item['status'] == 'Open':
                    InterbranchOrder.objects.filter(id=item['id']).update(status='Printed')
                data_list.append(item['id'])
            elif action == 'cancel':
                if item['status'] == 'Open' or item['status'] == 'Printed':
                    InterbranchOrder.objects.filter(id=item['id']).update(status='Cancelled')
            elif action == 'fulfill':
                if item['status'] == 'Printed':
                    InterbranchOrder.objects.filter(id=item['id']).update(status='Fulfilled')
            elif action == 'receive':
                if item['status'] == 'Fulfilled':
                    InterbranchOrder.objects.filter(id=item['id']).update(status='Finish')

        return json_response(code=0, msg='Success', data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)

@login_required
def redirect_interbranch_order_print(request):
    try:
        id_str = request.GET.get('id_str', '')
        id_str = id_str[1:]
        id_list = id_str.split("-")
        interbranch_orders = InterbranchOrder.objects.filter(id__in=id_list)
        # for item in checkdata_list:
        #     if item['status'] == 'Open':
        #         InterbranchOrder.objects.filter(id=item['id']).update(status='Printed')

        return render(request, "interbranchorder_list_print.html", {
            "interbranch_orders": interbranch_orders,
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_STOCK', login_url='/oms/forbid/')
def redirect_interbranch_order_receive(request):
    try:
        re_inte_order_number = request.POST.get('re_inte_order_number', '')
        re_issuing_warehouse = request.POST.get('re_issuing_warehouse', '')
        re_receiving_warehouse = request.POST.get('re_receiving_warehouse', '')
        re_frame_sku = request.POST.get('re_frame_sku', '')
        #re_lens_sku = request.POST.get('re_lens_sku', '')
        re_quantity = request.POST.get('re_quantity', '')
        re_act_quantity = request.POST.get('re_act_quantity', '')
        re_comments = request.POST.get('re_comments', '')
        id = request.POST.get('id', '')

        if re_act_quantity == '':
            return json_response(code=-1, msg='参数不能为空')

        # 成品库移单入库 start
        issuing_invsws = inventory_struct_warehouse.objects.get(sku=re_frame_sku.upper(), warehouse_code=re_issuing_warehouse)
        i_diff_quantity = issuing_invsws.quantity - int(re_quantity)
        if i_diff_quantity < 0:
            i_diff_quantity = 0
        issuing_invsws.quantity = i_diff_quantity
        issuing_invsws.save()
        try:
            i_whs = warehouse.objects.get(code=re_issuing_warehouse)
        except Exception as e:
            return json_response(code=-1, msg='仓库不存在')

        products = product_frame.objects.filter(sku=re_frame_sku.upper())
        if len(products) == 0:
            return json_response(code=-1, msg='产品不存在，请确认')

        prod = products[0]
        p_number = datetime.datetime.now().strftime('%Y%m%d')
        # 创建出库inventory_delivery记录 start
        invd = inventory_delivery()
        invd.doc_number = p_number
        invd.warehouse = i_whs
        invd.warehouse_code = i_whs.code
        invd.warehouse_name = i_whs.name
        invd.sku = re_frame_sku.upper()
        invd.quantity = re_quantity
        invd.name = prod.name
        invd.doc_type = "ALLOTTED_OUT"
        invd.lab_number = ""
        invd.user_id = request.user.id
        invd.user_name = request.user.username
        invd.comments = ""
        invd.save()
        # 创建出库inventory_delivery记录 end
        receiving_invsws = inventory_struct_warehouse.objects.filter(sku=re_frame_sku.upper(),
                                                                warehouse_code=re_receiving_warehouse)
        try:
            wh = warehouse.objects.get(code=re_receiving_warehouse)
        except Exception as e:
            return json_response(code=-1, msg='仓库不存在')

        if len(receiving_invsws) == 0:
            receiving_invsw = inventory_struct_warehouse()
            receiving_invsw.sku = re_frame_sku.upper()
            receiving_invsw.warehouse_code = wh.code
            receiving_invsw.warehouse_name = wh.name
            receiving_invsw.name = prod.name
            receiving_invsw.quantity = int(re_act_quantity)
            receiving_invsw.save()
        else:
            receiving_invsw = receiving_invsws[0]
            receiving_invsw.quantity = receiving_invsw.quantity + int(re_act_quantity)
            receiving_invsw.save()
        # 创建出库inventory_receipt记录 start
        invr = inventory_receipt()
        invr.doc_number = p_number
        invr.warehouse = wh
        invr.warehouse_code = wh.code
        invr.warehouse_name = wh.name
        invr.sku = re_frame_sku.upper()
        invr.quantity = int(re_act_quantity)
        invr.price = 0
        invr.name = prod.name
        invr.doc_type = "ALLOTTED_IN"
        invr.lab_number = ""

        invr.user_id = request.user.id
        invr.user_name = request.user.username
        invr.comments = re_comments
        invr.save()
        # 创建出库inventory_receipt记录 end
        InterbranchOrder.objects.filter(id=id).update(status='Finish')
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_BOM_NEW', login_url='/oms/forbid/')
def redirect_stock_bom_order_new(request):
    try:
        # 获取所有sku
        product_frame_list = []
        frame_list = []
        product_frame_lists = product_frame.objects.filter()
        for item in product_frame_lists:
            if item.product_type == 'FRAME':
                frame_list.append(item.sku)
            elif item.product_type == 'STKG':
                product_frame_list.append(item.sku)

        sku_list = product_lens.objects.values('sku', 'name')
        return render(request, "stockorder_bom_new.html", {
            "sku_list": sku_list,
            "product_frame_list": product_frame_list,
            "frame_list": frame_list
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_BOM_NEW', login_url='/oms/forbid/')
def redirect_stock_bom_order_save(request):
    try:
        product_sku = request.POST.get('product_sku', '')
        frame_sku = request.POST.get('frame_sku', '')
        frame_qty = request.POST.get('frame_qty', '')
        od_lens_sku = request.POST.get('od_lens_sku', '')
        od_lens_name = request.POST.get('od_lens_name', '')
        od_lens_sph = request.POST.get('od_lens_sph', '0')
        od_lens_cyl = request.POST.get('od_lens_cyl', '0')
        od_lens_qty = request.POST.get('od_lens_qty', '0')
        os_lens_sku = request.POST.get('os_lens_sku', '')
        os_lens_name = request.POST.get('os_lens_name', '')
        os_lens_sph = request.POST.get('os_lens_sph', '0')
        os_lens_cyl = request.POST.get('os_lens_cyl', '0')
        os_lens_qty = request.POST.get('os_lens_qty', '0')
        comments = request.POST.get('comments', '')
        stock_bom_structs = StockBomStruct.objects.filter(product_sku=product_sku)
        if len(stock_bom_structs) > 0:
            return json_response(code=-1, msg='该成镜SKU已存在！')

        new_bom = StockBomStruct()
        new_bom.product_sku = product_sku
        new_bom.product_qty = frame_qty
        new_bom.frame = frame_sku.upper()
        new_bom.frame_qty = frame_qty
        new_bom.od_lens_sku = od_lens_sku
        new_bom.od_lens_name = od_lens_name
        new_bom.od_sph = od_lens_sph
        new_bom.od_cyl = od_lens_cyl
        new_bom.od_lens_qty = od_lens_qty
        new_bom.os_lens_sku = os_lens_sku
        new_bom.os_lens_name = os_lens_name
        new_bom.os_sph = os_lens_sph
        new_bom.os_cyl = os_lens_cyl
        new_bom.os_lens_qty = os_lens_qty
        new_bom.comments = comments
        new_bom.user_name = request.user.username
        new_bom.user_id = request.user.id
        new_bom.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
def redirect_stock_bom_order_new_data(request):
    data_list = []
    try:
        page = request.GET.get('page', '1')
        limit = request.GET.get('limit', '30')
        page = int(page)
        start = (page-1) * int(limit)
        end = page * int(limit)
        stock_orders = StockBomStruct.objects.filter().order_by("-id")
        total = len(stock_orders)
        fsi_list = stock_orders[start: end]
        for item in fsi_list:
            data_list.append({
                "id": item.id,
                "product_sku": item.product_sku,
                "product_qty": item.product_qty,
                "frame": item.frame,
                "frame_qty": item.frame_qty,
                "od_lens_sku": item.od_lens_sku,
                "od_lens_name": item.od_lens_name,
                "od_lens_sph": str(item.od_sph),
                "od_lens_cyl": str(item.od_cyl),
                "od_len_qty": str(item.od_lens_qty),
                "os_lens_sku": item.os_lens_sku,
                "os_lens_name": item.os_lens_name,
                "os_lens_sph": str(item.os_sph),
                "os_lens_cyl": str(item.os_cyl),
                "os_len_qty": str(item.os_lens_qty),
                "user_name": item.user_name,
                "comments": item.comments,
                "update_date": (item.updated_at+datetime.timedelta(hours=+8)).strftime("%Y-%m-%d %H:%M:%S")
            })
        return json_response_page(code=0, msg='', count=total, data=data_list)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('stockorder.STOCKORDER_BOM_NEW', login_url='/oms/forbid/')
def redirect_stock_bom_order_update(request):
    try:
        product_id = request.POST.get('product_id', '')
        product_sku = request.POST.get('product_sku', '')
        frame_sku = request.POST.get('frame_sku', '')
        frame_qty = request.POST.get('frame_qty', '')
        od_lens_sku = request.POST.get('od_lens_sku', '')
        od_lens_name = request.POST.get('od_lens_name', '')
        od_lens_sph = request.POST.get('od_lens_sph', '0')
        od_lens_cyl = request.POST.get('od_lens_cyl', '0')
        od_lens_qty = request.POST.get('od_lens_qty', '0')
        os_lens_sku = request.POST.get('os_lens_sku', '')
        os_lens_name = request.POST.get('os_lens_name', '')
        os_lens_sph = request.POST.get('os_lens_sph', '0')
        os_lens_cyl = request.POST.get('os_lens_cyl', '0')
        os_lens_qty = request.POST.get('os_lens_qty', '0')
        comments = request.POST.get('comments', '')

        new_bom = StockBomStruct.objects.get(id=product_id)
        new_bom.product_sku = product_sku
        new_bom.product_qty = frame_qty
        new_bom.frame = frame_sku.upper()
        new_bom.frame_qty = frame_qty
        new_bom.od_lens_sku = od_lens_sku
        new_bom.od_lens_name = od_lens_name
        new_bom.od_sph = od_lens_sph
        new_bom.od_cyl = od_lens_cyl
        new_bom.od_lens_qty = od_lens_qty
        new_bom.os_lens_sku = os_lens_sku
        new_bom.os_lens_name = os_lens_name
        new_bom.os_sph = os_lens_sph
        new_bom.os_cyl = os_lens_cyl
        new_bom.os_lens_qty = os_lens_qty
        new_bom.comments = comments
        new_bom.user_name = request.user.username
        new_bom.user_id = request.user.id
        new_bom.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)