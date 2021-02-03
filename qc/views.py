# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.db import transaction
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

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

import oms.const
from oms.models.utilities_models import utilities
from .models import *
from .forms import *

from util.response import response_message

from oms.controllers.lab_order_controller import lab_order_controller
from oms.models.glasses_models import received_glasses_control
from qc.models import prescripiton_actual
from qc.models import glasses_final_inspection,PreliminaryPrescripitonActual
from oms.models import order_models
from wms.models import channel, warehouse, inventory_delivery_control, inventory_delivery_channel_controller, inventory_struct, inventory_delivery, product_lens,inventory_struct_lens,inventory_delivery_lens_controller,inventory_delivery_lens,product_frame
from qc.models import glasses_final_inspection_technique
from workshop.models import Assembler
from django.db import connections
from oms.views import namedtuplefetchall, status_choice
import datetime
import re
import time
import csv, codecs

def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('qc.FINAL_INSPECTION', login_url='/oms/forbid/')
def redirect_qc_glasses_final_inspection_technique(request):
    form = None
    if request.method == 'POST':  # 当提交表单时
        pass
    else:  # 当正常访问时
        # form = AddForm()
        form = None
    return render(request, 'qc_glasses_final_inspection_technique_create.html', {'form': form})


def final_inspection_change_status(request, form, lbo, gfit):
    form_clean = form.clean()
    print (form_clean['od_sub_mirrors_height'])
    print (form_clean['os_sub_mirrors_height'])
    gfit.lab_number = lbo.lab_number
    gfit.laborder_entity = lbo
    gfit.laborder_id = lbo.id
    gfit.user_id = request.user.id
    gfit.user_name = request.user.username
    if '双光' in lbo.act_lens_name:
        if lbo.is_singgle_pd:
            gfit.npd = form_clean['npd']
            gfit.pd = int(form_clean['npd']) + 4
        else:
            gfit.od_npd = form_clean['od_npd']
            gfit.os_npd = form_clean['os_npd']
            gfit.od_pd = int(form_clean['od_npd']) + 2
            gfit.os_pd = int(form_clean['os_npd']) + 2
    else:
        if lbo.is_singgle_pd:
            gfit.npd = form_clean['npd']
            gfit.pd = form_clean['pd']
        else:
            gfit.od_pd = form_clean['od_pd']
            gfit.os_pd = form_clean['os_pd']
            gfit.od_npd = form_clean['od_npd']
            gfit.os_npd = form_clean['os_npd']

    gfit.is_singgle_pd = lbo.is_singgle_pd
    gfit.od_prism = form_clean['od_prism']
    gfit.od_base = form_clean['od_base']
    gfit.os_prism = form_clean['os_prism']
    gfit.os_base = form_clean['os_base']

    gfit.od_prism1 = form_clean['od_prism1']
    gfit.od_base1 = form_clean['od_base1']
    gfit.os_prism1 = form_clean['os_prism1']
    gfit.os_base1 = form_clean['os_base1']

    gfit.od_asmbl_seght = form_clean['od_asmbl_seght']
    gfit.os_asmbl_seght = form_clean['os_asmbl_seght']

    gfit.blue_blocker = form_clean['blue_blocker']
    gfit.polarized = form_clean['polarized']
    gfit.light_responsive = form_clean['light_responsive']
    gfit.light_responsive_color = form_clean['light_responsive_color']
    gfit.co = form_clean['co']
    gfit.tint = form_clean['tint']

    gfit.tint_deepness = form_clean['tint_deepness']
    gfit.is_gradient = form_clean['is_gradient']

    gfit.is_d_thin = form_clean['is_d_thin']

    gfit.is_qualified = form_clean['is_qualified']
    gfit.comments = form_clean['comments']

    gfit.assembler_id = form_clean['assembler_id']
    # add lee 2020.8.4
    gfit.cutting_edge_user_id = form_clean['cutting_edge_user_id']
    gfit.beauty_user_id = form_clean['beauty_user_id']
    # end
    gfit.od_sub_mirrors_height = form_clean['od_sub_mirrors_height']
    gfit.os_sub_mirrors_height = form_clean['os_sub_mirrors_height']
    gfit.is_special_handling = form_clean['is_special_handling']
    gfit.od_tint_deepness = form_clean['od_tint_deepness']
    gfit.os_tint_deepness = form_clean['os_tint_deepness']
    gfit.clipon_qty = form_clean['clipon_qty']
    gfit.is_polishing = form_clean['is_polishing']
    gfit.is_near_light = form_clean['is_near_light']
    gfit.coatings = form_clean['coatings']
    gfit.save()
    tloc = tracking_lab_order_controller()
    if form_clean['is_qualified']:
        lbo.status = "FINAL_INSPECTION_YES"
        tloc.tracking(lbo, request.user, lbo.status, "终检合格", gfit.comments)
    else:
        lbo.status = "FINAL_INSPECTION_NO"
        tloc.tracking(lbo, request.user, lbo.status, "终检不合格", gfit.comments)
    lbo.save()
    # 记录当前的装配师、整型师
    request.session['session_assembler_id']=gfit.assembler_id
    request.session['session_beauty_user_id']=gfit.beauty_user_id

@login_required
@permission_required('qc.FINAL_INSPECTION', login_url='/oms/forbid/')
def redirect_qc_glasses_final_inspection_technique_create(request):
    '''
    技术指标
    :param request:
    :return:
    '''
    assemblers = None
    form = None
    lbo = None
    exist = False
    res_msg = response_message()
    _form_data = {}#用来给laborder_detail传数据
    try:
        with transaction.atomic():
            if request.method == 'POST':  # 当提交表单时
                lab_number = request.POST.get("lab_number")
                repair = request.POST.get("repair")
                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_number)
                if len(lbos) == 1:
                    lbo = lbos[0]

                    # 用来到wms_product_frame中查找sku_specs字段（警示信息）
                    caution_info = product_frame.objects.get(sku=lbo.frame)
                    _form_data['caution_info'] = caution_info.sku_specs

                try:
                    assemblers = Assembler.objects.filter(is_enabled=True).order_by('id')
                except Exception as e:
                    res_msg.code = -1
                    res_msg.message = "装配师表错误"

                # 终检不合格可以修正为终检合格
                status_tuple = ('FINAL_INSPECTION', 'FINAL_INSPECTION_NO', 'FINAL_INSPECTION_YES')
                if (lbo.status in status_tuple) or lbo.vendor == '1000':
                    form = form_glasses_final_inspection_technique_create(request.POST)
                    if form.is_valid():
                        if lbo.status == "FINAL_INSPECTION" or lbo.vendor == '1000':
                            try:
                                gfit = glasses_final_inspection_technique.objects.get(laborder_id=lbo.id)
                            except Exception as e:
                                gfit = glasses_final_inspection_technique()
                            final_inspection_change_status(request, form, lbo, gfit)
                        else:
                            if repair == "on":
                                gfit = glasses_final_inspection_technique.objects.get(laborder_id=lbo.id)
                                final_inspection_change_status(request, form, lbo, gfit)
                            else:
                                res_msg.code = -2
                                res_msg.message = "请勾选【误判修复】选项"
                    else:
                        res_msg.code = -5
                        res_msg.message = "表单数据未通过合法性检查! %s" % form.errors
                else:
                    res_msg.code = 4
                    res_msg.message = "当前订单状态【%s】不能更改为【终检合格】" % lbo.get_status_display()

                lbo = None

            else:
                lab_number = request.GET.get('lab_number', '')
                if not lab_number == "":
                    loc = lab_order_controller()
                    lbos = loc.get_by_entity(lab_number)
                    if len(lbos) == 1:
                        lbo = lbos[0]
                        lab_number = lbo.lab_number
                        exist = True

                        # 用来到wms_product_frame中查找sku_specs字段（警示信息）
                        caution_info = product_frame.objects.get(sku=lbo.frame)
                        _form_data['caution_info'] = caution_info.sku_specs

                    try:
                        form = glasses_final_inspection_technique.objects.get(lab_number=lab_number)
                    except Exception as e:
                        res_msg.capture_execption(e)

                    try:
                        LabOrder.objects.get(lab_number=lab_number)
                    except Exception as e:
                        res_msg.code = -1
                        res_msg.message = "输入的订单号不存在"

                    try:
                        assemblers = Assembler.objects.filter(is_enabled=True).order_by('id')
                    except Exception as e:
                        res_msg.code = -1
                        res_msg.message = "装配师表错误"
                else:
                    res_msg.code = -1
                    res_msg.message = "扫描&输入工厂订单号"

    except Exception as e:
        logging.debug("Error====>%s" % e.message)
        res_msg.capture_execption(e)
        res_msg.exception = "Error====>%s" % e
    _form_data['laborder'] = lbo#用来给laborder_detail传数据
    # print("session_assembler_id",request.session['session_assembler_id'])
    print("session")
    print(request.session.get("session_assembler_id"))
    return render(request, 'qc_glasses_final_inspection_technique_create.html', {
        'form': form,
        'lbo': lbo,
        'error_code': res_msg.code,
        'error_message': res_msg.message,
        'method': request.method,
        'exist': exist,
        'form_data':_form_data,
        'assemblers':assemblers,
    })

@login_required
@permission_required('qc.FINAL_INSPECTION', login_url='/oms/forbid/')
def qc_glasses_final_inspection_technique_list(request):

    # 定义变量
    rm = response_message()
    _form_data = {}
    # 定义参数
    vendor_list = []
    for vcl in LabOrder.VENDOR_CHOICES:
        vc = status_choice()
        vc.key = vcl[0]
        vc.value = vcl[1]
        vendor_list.append(vc)

    assembler_list = []
    assemblers = Assembler.objects.filter(is_enabled=True).order_by('id')
    for assembler in assemblers:
        vc = status_choice()
        vc.key = assembler.user_code
        vc.value = assembler.user_name
        assembler_list.append(vc)
    #vendor_list = ['1','2','3','4','5','6','7','8','9','10','1000']
    _form_data['vendor_list'] = vendor_list
    _form_data['assembler_list'] = assembler_list
    # 获取参数
    lab_number = request.GET.get('lab_number', '')
    _form_data['lab_number'] = lab_number
    start_time = request.GET.get('start_time', '')
    _form_data['start_time'] = start_time
    end_time = request.GET.get('end_time', '')
    _form_data['end_time'] = end_time
    vendor = request.GET.get('vendor', 'all')
    _form_data['vendor'] = vendor

    assembler = request.GET.get('assembler', 'all')
    _form_data['assembler'] = assembler
    page = request.GET.get('page', 1)
        # GET参数
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string

    # 条件搜索
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    where = 'where t1.is_qualified = 1 '
    # VD不为空
    if not vendor == 'all':
        where += 'and t2.vendor = "%s" ' % vendor
    # 开始时间不为空
    if start_time == '':
        where += 'and t1.updated_at >= "%s" ' % today
        _form_data['start_time'] = today
    else:
        where += 'and t1.updated_at >= "%s" ' % start_time
    # 结束时间不为空
    if not end_time == '':
        where += 'and t1.updated_at <= "%s" ' % end_time

    if not assembler == 'all':
        where += 'and t3.user_code = "%s"' % assembler

    # 搜索框单号不为空
    if not lab_number == '':
        where = 'where t1.lab_number = "%s"' % lab_number

    try:
        sql = """
                select t1.id,t1.lab_number,t1.created_at,t1.updated_at,t1.user_name,t1.assembler_id,t2.vendor, t3.user_name as assembler_user_name
                from qc_glasses_final_inspection_technique as t1
                left join oms_laborder as t2
                on t1.lab_number = t2.lab_number
                LEFT JOIN workshop_assembler AS t3 ON t1.assembler_id = t3.id
                %s
                order by t1.id desc
            """ % where
        logging.debug(sql)
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            received_list = namedtuplefetchall(cursor)

        _form_data['total'] = len(received_list)
        paginator = Paginator(received_list, 20)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        return render(request, 'qc_glasses_final_inspection_technique_list.html',
                      {
                          "list": items,
                          'form_data': _form_data,
                          'paginator': paginator,
                          'requestUrl': '/qc/qc_glasses_final_inspection_technique_list/',
                          'query_string': query_string,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('qc_glasses_final_inspection_technique_list'),
                      })



@login_required
@permission_required('qc.FINAL_INSPECTION', login_url='/oms/forbid/')
def redirect_qc_glasses_final_inspection_visual_create(request):
    _form_data = {}
    lab_number = ''
    comments = ''
    checkd_list = []
    activeName = []
    lbo = None
    exist = False
    res_msg = response_message()
    if request.method == 'POST':  # 当提交表单时
        lab_number = request.POST.get("lab_number", "")
        is_frame = request.POST.get("is_frame", "")
        is_parts = request.POST.get("is_parts", "")
        is_lens = request.POST.get("is_lens", "")
        is_assembling = request.POST.get("is_assembling", "")
        is_plastic = request.POST.get("is_plastic", "")
        comments = request.POST.get("comments", "")
        checkd_list = request.POST.getlist('checkd_list[]')
        if not lab_number == "":
            lab_number = lab_number.replace(" ", "")
            gfavs = glasses_final_appearance_visual.objects.get_or_create(lab_number=lab_number)
            gfav = gfavs[0]
            gfav.is_frame = is_frame
            gfav.is_parts = is_parts
            gfav.is_lens = is_lens
            gfav.is_assembling = is_assembling
            gfav.is_plastic = is_plastic
            gfav.comments = comments
            gfav.user_id = request.user.id
            gfav.user_name = request.user.username
            gfav.save()
            glasses_unqualified_items.objects.filter(appearance_id=gfav.id).update(is_enabled=0)
            for item in checkd_list:
                gui = glasses_unqualified_items()
                gui.appearance_id = gfav.id
                gui.item_id = int(item)
                gui.user_id = request.user.id
                gui.user_name = request.user.username
                gui.save()
            return JsonResponse(res_msg.response_dict(code=0, msg='操作成功'))
    else:
        # 当正常访问时
        lab_number = request.GET.get('lab_number', '')
        if not lab_number == "":
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_number)
            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
                exist = True

                # 用来到wms_product_frame中查找sku_specs字段（警示信息）
                caution_info = product_frame.objects.get(sku=lbo.frame)
                _form_data['caution_info'] = caution_info.sku_specs

            try:
                LabOrder.objects.get(lab_number=lab_number)
            except Exception as e:
                res_msg.code = -1
                res_msg.message = "输入的订单号不存在"
            try:
                gfavs = glasses_final_appearance_visual.objects.filter(lab_number=lab_number)
                if len(gfavs) > 0:
                    gfav = gfavs[0]
                    comments = gfav.comments
                    if not gfav.is_frame:
                        activeName.append('1')
                    if not gfav.is_parts:
                        activeName.append('2')
                    if not gfav.is_lens:
                        activeName.append('3')
                    if not gfav.is_assembling:
                        activeName.append('4')
                    if not gfav.is_plastic:
                        activeName.append('5')
                    guis = glasses_unqualified_items.objects.filter(appearance_id=gfav.id, is_enabled=1)
                    for gui in guis:
                        checkd_list.append(str(gui.item_id))
            except Exception as e:
                res_msg.capture_execption(e)

        else:
            res_msg.code = -1
            res_msg.message = "扫描&输入工厂订单号"

        return render(request,
                      'qc_glasses_final_inspection_visual_create.html',
                      {
                          'form_data': _form_data,
                          'lbo': lbo,
                          'error_code': res_msg.code,
                          'error_message': res_msg.message,
                          'method': request.method,
                          'exist': exist,
                          'checkd_list': json.dumps(checkd_list),
                          'comments': comments,
                          'activeName':json.dumps(activeName),
                      })


@login_required
@permission_required('qc.LENS_REGISTRATION', login_url='/oms/forbid/')
def redirect_lens_registration(request):
    '''
    来片登记
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}  # 字典，相当于hashMap

    _form_data['request_feature'] = 'Lens Registration'
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
                logging.debug('----------------------------------------')
                lrc = lens_registration_control()
                # lens_registration_control.add 已添加事务
                rm = lrc.add(
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

        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

            # 用来到wms_product_frame中查找sku_specs字段（警示信息）
            caution_info = product_frame.objects.get(sku=lbo.frame)
            _form_data['caution_info'] = caution_info.sku_specs

        return render(request, "lens_registration.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('lens_registration'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('lens_registration'),
                      })


@login_required
@permission_required('qc.PRELIMINARY_CHECKING', login_url='/oms/forbid/')
def redirect_preliminary_checking(request):
    '''
    初检
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

            # 用来到wms_product_frame中查找sku_specs字段（警示信息）
            caution_info = product_frame.objects.get(sku=lbo.frame)
            _form_data['caution_info'] = caution_info.sku_specs

            lbo = LabOrder.objects.get(lab_number=lab_number)
            pre_pas = PreliminaryPrescripitonActual.objects.filter(lab_number=lab_number).order_by("-id")
            pre_pa = None
            if len(pre_pas) > 0:
                pre_pa = pre_pas[0]

            _form_data['pre_pa'] = pre_pa
            _form_data['laborder'] = lbo
            special_handling = lbo.special_handling if lbo.special_handling else ''
            _form_data['special_handling'] = special_handling.replace("\n", "").replace("\t", "").replace("\r", "")


        return render(request, "preliminary_checking.html",
                      {
                          'form_data': _form_data,
                          'item':lbo,
                          'requestUrl': reverse('preliminary_checking'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('preliminary_checking'),
                      })


@login_required
@permission_required('qc.RECEIVED_LENS', login_url='/oms/forbid/')
def redirect_received_lens(request):
    '''
    成镜收货单
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Received Glasses'
    items = []
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

        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

        return render(request, "received_lens.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('received_lens'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('received_lens'),
                      })


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_glasses_return(request):
    '''
    成镜退货单
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Return Glasses'
    items = []
    lbo = None
    try:
        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')
            qualified = request.POST.get('qualified', '')
            reason_code = request.POST.get('reason_code', '')
            reason = request.POST.get('reason', '')
            lens_return = request.POST.get('lens_return', '')
            comments = request.POST.get('comments', '')
            frame_reason = request.POST.get('frame_reason', '')
            frame_comments = request.POST.get('frame_comments', '')
            assembler = request.POST.get('assembler', '')
            lens_check = request.POST.get('lens_check', '')
            frame_check = request.POST.get('frame_check', '')
            assembler_user_code = request.POST.get('assembler_user_code', '')
            assembler_user_name = request.POST.get('assembler_user_name', '')
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

                data_dict = {
                    'lab_number': lab_number,
                    'is_qualified': is_qualified,
                    'reason_code': reason_code,
                    'reason': reason,
                    'lens_return': lens_return,
                    'comments': comments,
                    'frame_reason':frame_reason,
                    'frame_comments': frame_comments,
                    'assembler': assembler,
                    'lens_check': lens_check,
                    'frame_check': frame_check,
                    'assembler_user_code': assembler_user_code,
                    'assembler_user_name': assembler_user_name
                }
                grc = glasses_return_control()

                rm = grc.add(request, data_dict)

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

            # 用来到wms_product_frame中查找sku_specs字段（警示信息）
            caution_info = product_frame.objects.get(sku=lbo.frame)
            _form_data['caution_info'] = caution_info.sku_specs

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo
        lens_reasons = LensReason.objects.filter(is_enabled=True).order_by("reason_code")
        frame_reasons = FrameReason.objects.filter(is_enabled=True).order_by("reason_code")
        assembler_lists = Assembler.objects.all()
        _form_data['assembler_lists'] = assembler_lists
        _form_data['lens_reasons'] = lens_reasons
        _form_data['frame_reasons'] = frame_reasons
        return render(request, "return_glasses.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('glasses_return'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('glasses_return'),
                      })


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_glasses_return_print(request):
    '''
    成镜退货单-打印
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Return Glasses'
    items = []
    lbo = None
    try:
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

            objs = glasses_return.objects.filter(lab_number=lab_number).order_by('-id')
            if len(objs) > 0:
                obj = objs[0]
                _form_data['obj'] = obj

                if obj.lens_return == '1':
                    _form_data['right'] = 1
                    _form_data['left'] = 0
                elif obj.lens_return == '2':
                    _form_data['right'] = 0
                    _form_data['left'] = 1
                else:
                    _form_data['right'] = 1
                    _form_data['left'] = 1
            else:
                return HttpResponse('没有找到对应的成镜返工单')

        return render(request, "return_glasses_print.html",
                      {
                          'form_data': _form_data,
                          'item': lbo,
                          'requestUrl': reverse('glasses_return_print'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('glasses_return'),
                      })


@login_required
@permission_required('qc.QUALITY_INSPECTION_REPORT', login_url='/oms/forbid/')
def redirect_quality_inspection_report(request):
    '''
        质检报告
        '''
    lbo = None
    pa = None
    gfit = None
    rm = response_message.response_dict()
    object_url = ''

    if request.method == 'POST':
        lab_number = ''
        # 获取order_number
        order_number = request.POST.get("order_number")
    else:
        order_number = request.GET.get("lab_number", "")

    # 查询 lab order
    if not order_number == '':
        loc = lab_order_controller()
        lbos = loc.get_by_entity(order_number)

        if len(lbos) == 1:
            lbo = lbos[0]
            lab_number = lbo.lab_number

        lbo = LabOrder.objects.get(lab_number=lab_number)

        # 如果lbo的状态
        if not lbo.status == 'FINAL_INSPECTION_YES' and not lbo.status == 'FINAL_INSPECTION_NO' \
                and not lbo.status == 'GLASSES_RETURN' and not lbo.status == 'GLASSES_RETURN' \
                and not lbo.status == 'PRE_DELIVERY' and not lbo.status == 'PICKING' \
                and not lbo.status == 'COLLECTION'  and not lbo.status == 'PRE_DELIVERY'\
                and not lbo.status == 'PICKING'  and not lbo.status == 'ORDER_MATCH'\
                and not lbo.status == 'BOXING'  and not lbo.status == 'SHIPPING'\
                and not lbo.status == 'ONHOLD'  and not lbo.status == 'CANCELLED'\
                and not lbo.status == 'REDO'  and not lbo.status == 'R2HOLD'\
                and not lbo.status == 'R2CANCEL'  and not lbo.status == 'CLOSED'\
                and not lbo.status == 'DELIVERED':
            rm['code'] = '-1'
            rm['message'] = "此订单状态不能查看终检报告"
            return JsonResponse(rm)

        # 查询镜片类型
        lens_sku = lbo.lens_sku

        lens_sku = lens_sku[1:2]

        #读取视频图片和其它
        l_as = laborder_accessories.objects.filter(lab_number=lab_number)
        if l_as.count() > 0:
            l_a = l_as[0]
            object_url = l_a.object_url

        if request.method == 'POST':
            try:
                gli = glasses_final_inspection.objects.get(laborder_id=lbo.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无终检数据"
                return JsonResponse(rm)

            try:
                pa = prescripiton_actual.objects.get(pk=gli.prescripiton_actual_entity.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无验光数据"
                return JsonResponse(rm)

            try:
                gfit = glasses_final_inspection_technique.objects.get(laborder_id=lbo.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无终检验光数据"
                logging.debug("err==================>%s" % e)
                return JsonResponse(rm)

        # if len(gfit) == 0:
        #     pass
        # else:
        #     gfi = gfit[0]
            assembler_name = ''
            if gfit.assembler_id:
                assembler = Assembler.objects.get(id=gfit.assembler_id)
                assembler_name = assembler.user_name

            return render(request, "quality_inspection_report_print.html", {
                "item": lbo,
                "lens_type": lens_sku,
                "pa": pa,
                "gfit": gfit,
                "object_url": object_url,
                "message": 'success',
                "assembler_name": assembler_name,
            })
        else:
            try:
                gli = glasses_final_inspection.objects.get(laborder_id=lbo.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无终检数据"
                #return JsonResponse(rm)

            try:
                pa = prescripiton_actual.objects.get(pk=gli.prescripiton_actual_entity.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无验光数据"
                #return JsonResponse(rm)

            try:
                gfit = glasses_final_inspection_technique.objects.get(laborder_id=lbo.id)
            except Exception as e:
                rm['code'] = '-1'
                rm['message'] = "无终检验光数据"
                logging.debug("err==================>%s" % e)
                #return JsonResponse(rm)

            return render(request, "quality_inspection_report.html", {
                "item": lbo,
                "lens_type": lens_sku,
                "pa": pa,
                "gfit": gfit,
                "object_url": object_url,
                "message": rm['message']
            })
    else:
        return render(request, "quality_inspection_report.html", {
            "lbo": lbo,
            "gfit": '',
            "message":'success',

        })


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_glasses_return_list(request):
    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Return Glasses List'
    order_number = request.GET.get('order_number', '')
    filter = request.GET.get('filter', '')
    page = request.GET.get('page', 1)
    currentPage = int(page)
    items_list = []
    lbo = None
    try:
        sql="""SELECT
                    l.id AS id,
                    g.lab_number AS lab_number,
                    l.frame AS frame,
                    l.frame_type AS frame_type,
                    l.lens_name AS lens_name,
                    l.act_lens_name AS act_lens_name,
                    l.status AS status,
                    l.vendor AS vendor,
                    l.workshop AS workshop,
                    CONVERT_TZ(l.create_at, @@session.time_zone,'+8:00') AS lab_created_at,
                    CONVERT_TZ(g.created_at, @@session.time_zone,'+8:00') AS glasses_created_at,
                    CASE WHEN g.idei_frame='' AND g.idei_lens_r='' AND g.idei_lens_l='' THEN '未操作'
                    WHEN g.idei_lens_r<>'' AND g.idei_lens_l<>'' THEN '镜片已出库'
                    WHEN g.idei_lens_r<>'' THEN '右片已出库'
                    WHEN g.idei_lens_l<>'' THEN '左片已出库'
                    WHEN g.idei_frame<>'' THEN '镜架已出库'
                    ELSE '已出库' END AS glasses_status
                FROM
                    qc_glasses_return AS g
                LEFT JOIN oms_laborder AS l ON g.lab_number = l.lab_number
            """

        if order_number != '':
            sql = sql + """ WHERE g.lab_number='%s' """ % order_number
        else:
            if filter == 'Processed':
                sql = sql + """ WHERE g.idei_frame<>'' OR g.idei_lens_r<>'' OR g.idei_lens_l<>''"""
            elif filter == 'Untreated':
                sql = sql + """ WHERE g.idei_frame='' AND g.idei_lens_r='' AND g.idei_lens_l=''"""

        sql = sql + """ ORDER BY l.id DESC"""

        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                items_list.append({
                    "id": item.id,
                    "lab_number": item.lab_number,
                    "frame": item.frame,
                    "frame_type": item.frame_type,
                    "lens_name": item.lens_name,
                    "act_lens_name": item.act_lens_name,
                    "status": item.status,
                    "vendor": item.vendor,
                    "workshop": item.workshop,
                    "lab_created_at": item.lab_created_at,
                    "glasses_created_at": item.glasses_created_at,
                    "glasses_status": item.glasses_status,
                })
            count = len(items_list)
            query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
            if query_string:
                query_string = '&' + query_string
            if count > 0:
                _form_data['total'] = len(items_list)

            paginator = Paginator(items_list, 50)  # Show 20 contacts per page

            try:
                items = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                items = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                items = paginator.page(paginator.num_pages)

        return render(request, "return_glasses_list.html",
                      {
                          "list": items,
                          'form_data': _form_data,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': '/qc/glasses_return_list/',
                          'filter': filter,
                          'query_string': query_string,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('glasses_return'),
                      })


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_glasses_return_detail(request):
    '''
    成镜退货详情
    :param request:
    :return:
    '''

    try:
        lab_number = request.POST.get("lab_number")
        time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
        all_wh = warehouse.objects.all()
        all_channel = channel.objects.all()
        sku_list = product_lens.objects.values('sku', 'name')
        lbo = LabOrder.objects.get(lab_number=lab_number)
        objs = glasses_return.objects.get(lab_number=lab_number)
        sph_list = None  # sph列表
        list_from = {}
        sph_list = inventory_struct_lens.objects.filter(sku=lbo.lens_sku).values('sph').distinct()
        logging.debug("sph_list_count" + str(len(sph_list)))
        list_from['sph_list'] = sph_list
        return render(request, "return_glasses_detail.html",
                      {
                          "time_now": time_now,
                          'item': objs,
                          'lbo': lbo,
                          'all_channel': all_channel,
                          'all_wh': all_wh,
                          'sku_list': sku_list,
                          'list_from': list_from,
                      })
    except Exception as e:
        logging.debug(e.message)
        return HttpResponse('No Data')


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_frame_delivery_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        _data = json.loads(form_data)
        gro = glasses_return.objects.filter(lab_number=_data.get("lab_number"))
        if gro.idei_frame != '':
            res_data['code'] = '-1'
            res_data['error'] = " 该订单镜架已报损出过库,请进行核实"
            return JsonResponse(res_data)

        invd_ctrl = inventory_delivery_control()
        rm = invd_ctrl.add(request, _data.get("p_number"), _data.get("wh_number"), _data.get("sku"),
                           _data.get("doc_type"), _data.get("quantity"), _data.get("comments"))

        delivery_doc_type = _data.get("doc_type")
        delivery_quantity = _data.get("quantity")
        if delivery_doc_type == 'FAULTY':
            idcc = inventory_delivery_channel_controller()
            invss = inventory_struct.objects.filter(sku=_data.get("sku"))
            invs = invss[0]
            al_quantity = invs.al_quantity
            diff_al_del_quantity = al_quantity - int(delivery_quantity)
            if diff_al_del_quantity >= 0:
                invs.al_quantity = diff_al_del_quantity
                invs.save()
            elif diff_al_del_quantity < 0 and al_quantity > 0:
                invs.al_quantity = 0
                invs.save()
                qty = abs(diff_al_del_quantity)
                res = idcc.add(request, _data.get("p_number"), _data.get("wh_channel"), _data.get("doc_type"),
                               _data.get("sku"), int(qty))

                if not res.code == 0:
                    res_data["code"] = -1
                    res_data["error"] = res.message
                    return JsonResponse(res_data)

            elif diff_al_del_quantity < 0 and al_quantity == 0:
                res = idcc.add(request, _data.get("p_number"), _data.get("wh_channel"), _data.get("doc_type"),
                               _data.get("sku"), int(_data.get("quantity")))
                if not res.code == 0:
                    res_data["code"] = -1
                    res_data["error"] = res.message
                    return JsonResponse(res_data)

        if rm.code == 0:
            invds = inventory_delivery.objects.filter(doc_number=_data.get("p_number")).order_by("-id")
            invd = invds[0]
            glasses_return.objects.filter(lab_number=_data.get("lab_number")).update(idei_frame=str(invd.id))
            res_data["code"] = 0
            res_data["error"] = "出库成功"
            return JsonResponse(res_data)

        res_data["code"] = -1
        res_data["error"] = "出库失败 请重试"
        return JsonResponse(res_data)

    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "出库失败 请重试"
        return JsonResponse(res_data)


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_get_lens_sph(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        _data = json.loads(form_data)
        sph_list = []
        #lbo = LabOrder.objects.get(lab_number=_data['lab_number'])
        sphs = inventory_struct_lens.objects.filter(sku=_data['sku']).values('sph').distinct()
        for item in sphs:
            sph_list.append(item)
        res_data['sph_list'] = sph_list
        res_data["code"] = 0
        res_data["error"] = "操作成功"
        return JsonResponse(res_data)
    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "操作失败"
        return JsonResponse(res_data)


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_get_lens_cyl(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        _data = json.loads(form_data)
        cyl_list = []
        cyls = inventory_struct_lens.objects.filter(sku=_data['sku'], sph=float(_data['sph'])).values('cyl').distinct()
        for item in cyls:
            cyl_list.append(item)

        res_data['cyl_list'] = cyl_list
        res_data["code"] = 0
        res_data["error"] = "操作成功"
        return JsonResponse(res_data)
    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "操作失败"
        return JsonResponse(res_data)


@login_required
@permission_required('qc.GLASSES_RETURN', login_url='/oms/forbid/')
def redirect_lens_delivery_submit(request):
    res_data = {}
    form_data = request.POST.get("form_data")
    try:
        _data = json.loads(form_data)
        gro = glasses_return.objects.get(lab_number=_data.get("lab_number"))
        if _data.get("lens_position") == "R" and gro.idei_lens_r != '':
            res_data['code'] = '-1'
            res_data['error'] = " 该订单右片已报损出过库,请进行核实"
            return JsonResponse(res_data)
        elif _data.get("lens_position") == "L" and gro.idei_lens_l != '':
            res_data['code'] = '-1'
            res_data['error'] = " 该订单左片已报损出过库,请进行核实"
            return JsonResponse(res_data)

        skus = product_lens.objects.filter(sku=_data.get('sku'))
        if skus.count() == 0:
            res_data['code'] = '-1'
            res_data['error'] = "未找到对应的SKU"
            return JsonResponse(res_data)

        # 数量验证
        isls = inventory_struct_lens.objects.filter(sku=_data.get('sku'), sph=_data.get('sph'), cyl=_data.get('cyl'))
        if isls.count() == 0:
            res_data['code'] = '-1'
            res_data['error'] = "镜片库存信息不存在"
            return JsonResponse(res_data)
        else:
            isl = isls[0]
            if isl.quantity - int(_data['quantity']) < 0:  # 可以在此设置警戒库存,目前可以出至0片
                res_data['code'] = '-1'
                res_data['error'] = "镜片库存数量不足"
                return JsonResponse(res_data)

        # 写入
        irlc = inventory_delivery_lens_controller()
        rm = irlc.add(request, _data.get('p_number'), _data.get('doc_type'), _data.get('wh_number'), _data.get('sku'), _data.get('sph'), _data.get('cyl'), 0, _data.get('quantity'), '',
                      _data.get('comments'), _data.get('lab_number'))

        # rm.code 值为 0 时  查询 inventory_receipt_lens
        # 显示当前入库全部数据 没有分页
        if rm.code == 0:
            # 获取今日入库单
            idls = inventory_delivery_lens.objects.filter(doc_number=_data.get('doc_number')).order_by("-id")
            idl = idls[0]
            #gro = glasses_return.objects.get(lab_number=_data.get("lab_number"))
            if _data.get("lens_position") == "R":
                gro.idei_lens_r = str(idl.id)
            else:
                gro.idei_lens_l = str(idl.id)
            gro.save()

            res_data["code"] = 0
            res_data["error"] = "出库成功"
            return JsonResponse(res_data)

        res_data["code"] = -1
        res_data["error"] = "出库失败 请重试"
        return JsonResponse(res_data)

    except Exception as e:
        res_data["code"] = -1
        res_data["error"] = "出库失败 请重试"
        return JsonResponse(res_data)


@login_required
@permission_required('qc.LENS_RETURN', login_url='/oms/forbid/')
def redirect_lens_return_list(request):
    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Return Lens List'
    order_number = request.GET.get('order_number', '')
    vendor = request.GET.get('vendor', 'all')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    page = request.GET.get('page', 1)
    currentPage = int(page)
    items_list = []
    lbo = None
    # VD列表
    vendors_choice_list = []
    for vcl in LabOrder.VENDOR_CHOICES:
        vc = status_choice()
        vc.key = vcl[0]
        vc.value = vcl[1]
        vendors_choice_list.append(vc)
    try:
        sql="""SELECT  
                    t0.id AS id,
                    t1.lab_number AS lab_number,
                    t0.frame AS frame,
                    t0.frame_type AS frame_type,
                    t0.lens_name AS lens_name,
                    t0.act_lens_name AS act_lens_name,
                    t0.status AS status,
                    t0.vendor AS vendor,
                    t0.workshop AS workshop,
                    CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00') AS lab_created_at,
                    CONVERT_TZ(t1.created_at, @@session.time_zone,'+8:00') AS lens_created_at,
                    t1.user_name,
                    t1.reason
            FROM qc_lens_return AS t1 LEFT JOIN  oms_laborder AS t0 ON t1.lab_number = t0.lab_number 
            """

        if order_number != '':
             sql = sql + """ WHERE t0.lab_number like '%%%s%%' """ % order_number
        else:
            if vendor != '' and vendor != 'all':
                sql = sql + """ WHERE t0.vendor ='%s' """ % vendor

            if vendor != '' and vendor != 'all' and start_date != '' and end_date != '':
                sql = sql + """ AND (date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00'))='%s' OR date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00')) BETWEEN '%s' AND '%s') """ % (start_date, start_date, end_date)
            else:
                if start_date != '' and end_date != '':
                    sql = sql + """ WHERE (date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00'))='%s' OR date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00')) BETWEEN '%s' AND '%s') """ % (
                    start_date, start_date, end_date)

        sql = sql + """ ORDER BY t0.id DESC"""
        print(sql)
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                items_list.append({
                    "id": item.id,
                    "lab_number": item.lab_number,
                    "frame": item.frame,
                    "frame_type": item.frame_type,
                    "lens_name": item.lens_name,
                    "act_lens_name": item.act_lens_name,
                    "status": item.status,
                    "vendor": item.vendor,
                    "workshop": item.workshop,
                    "lab_created_at": item.lab_created_at,
                    "lens_created_at": item.lens_created_at,
                    "username": item.user_name,
                    "lens_reason": item.reason,
                })
            count = len(items_list)
            query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
            if query_string:
                query_string = '&' + query_string
            if count > 0:
                _form_data['total'] = len(items_list)

            paginator = Paginator(items_list, 50)  # Show 20 contacts per page

            try:
                items = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                items = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                items = paginator.page(paginator.num_pages)

        return render(request, "return_lens_list.html",
                      {
                          "list": items,
                          'form_data': _form_data,
                          'vendors_choices': vendors_choice_list,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': '/qc/lens_return_list/',
                          'start_date': start_date,
                          'end_date': end_date,
                          'vendor': vendor,
                          'order_number': order_number,
                          'query_string': query_string,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('lens_return'),
                      })


@login_required
@permission_required('qc.LENS_RETURN', login_url='/oms/forbid/')
def redirect_lens_return_list_csv(request):
    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Return Lens List'
    order_number = request.GET.get('order_number', '')
    vendor = request.GET.get('vendor', 'all')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    try:
        sql="""SELECT
                    t0.id AS id,
                    t1.lab_number AS lab_number,
                    t0.frame AS frame,
                    t0.frame_type AS frame_type,
                    t0.lens_name AS lens_name,
                    t0.act_lens_name AS act_lens_name,
                    t0.status AS status,
                    t0.vendor AS vendor,
                    t0.workshop AS workshop,
                    CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00') AS lab_created_at,
                    CONVERT_TZ(t1.created_at, @@session.time_zone,'+8:00') AS lens_created_at,
                    t1.user_name,
                    t1.reason
            FROM qc_lens_return AS t1 LEFT JOIN  oms_laborder AS t0 ON t1.lab_number = t0.lab_number
            """

        if order_number != '':
             sql = sql + """ WHERE t0.lab_number like '%%%s%%' """ % order_number
        else:
            if vendor != '' and vendor != 'all':
                sql = sql + """ WHERE t0.vendor ='%s' """ % vendor

            if vendor != '' and vendor != 'all' and start_date != '' and end_date != '':
                sql = sql + """ AND (date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00'))='%s' OR date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00')) BETWEEN '%s' AND '%s') """ % (start_date, start_date, end_date)
            else:
                if start_date != '' and end_date != '':
                    sql = sql + """ WHERE (date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00'))='%s' OR date(CONVERT_TZ(t0.create_at, @@session.time_zone,'+8:00')) BETWEEN '%s' AND '%s') """ % (
                    start_date, start_date, end_date)

        sql = sql + """ ORDER BY t0.id DESC"""

        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)
            response = HttpResponse(content_type='text/csv')
            file_name = 'lens_return_list'
            response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
            response.write(codecs.BOM_UTF8)

            writer = csv.writer(response)
            # 在下面添加要导出的属性即可
            writer.writerow([
                'id', '订单号','镜架', '计划镜片', '镜片', '类型',
                '下达日期', '状态', 'VD', 'WS', '镜片退货日期', '镜片原因', '操作人'])

            for item in _items:
                writer.writerow([
                    item.id, item.lab_number, item.frame, item.lens_name, item.act_lens_name, item.frame_type,
                    item.lab_created_at,item.status, item.vendor, item.workshop,item.lens_created_at, item.reason,
                    item.user_name
                ])

        return response


    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)

