# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.http import HttpResponse, JsonResponse
from .models import *
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.utils import timezone

from util.format_helper import *
from util.dict_helper import dict_helper
import csv
import codecs
import urllib2
import re
import logging
import oms.const
import collections
from oms.models.glasses_models import received_glasses
from report.models import lens_report_control
from merchandising.const import simple_general_query
import const

from util.time_delta import *
from django.db import connections, transaction
from collections import Counter
from .const import SQL_FLOW_REPORT, SQL_PGORDER_COUPON_REPORT, VD4_PURCHASE_DIFF_SQL, VD9_PURCHASE_DIFF_SQL, ARRIVAL_TIME_DIFF_SQL, DOCTOR_LAB_SQL


# Create your views here.
def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


def redirect_laborder_statistical_analysis(request):
    _form_data = {}

    sal = statistical_analysis_laborder()

    _form_data['time_dimentions_new'] = sal.time_dimentions_new()
    _form_data['time_dimentions_week'] = sal.time_dimentions_week()
    _form_data['time_dimentions_month'] = sal.time_dimentions_month()
    _form_data['time_dimentions_all'] = sal.time_dimentions_all()

    _form_data['status_dimentions'] = sal.status_dimentions()

    return render(request, "laborder_statistical_analysis.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_laborder_lens_registration_analysis(request):
    rm = response_message()

    _form_data = {}

    lrc = None
    lrc = lens_report_control()
    rm = lrc.generate_report_front()

    return render(request, "laborder_lens_registration_analysis.html",
                  {
                      'form_data': _form_data,
                      'rm': rm,
                      'objects': rm.obj,
                  })


@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_web_order_report_v2(request):
    rm = response_message()
    message = None
    try:
        if request.method == 'POST':
            filter = request.POST.get('filter')
            orc = order_report_control()
            rm = orc.generate_v2(filter)

            data = {}
            data['json_body'] = rm.obj

            return HttpResponse(json.dumps(data, cls=DateEncoder))

        else:
            message = '正在生成报表, 请稍后 ....'

        return render(request, 'web_order_report.html',
                      {

                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_shipping_speed_report(request):
    # 查询
    try:
        with connections['default'].cursor() as cursor:
            # 单光
            sql_d_good = SQL_SHIPPING_SPEED % (
                'D', 'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) <= 2 AND status = \'SHIPPING\'')
            sql_d_average = SQL_SHIPPING_SPEED % ('D',
                                                  'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) > 2 AND TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) <= 5 AND status = \'SHIPPING\'')
            sql_d_poor = SQL_SHIPPING_SPEED % (
                'D', 'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) > 5 AND status = \'SHIPPING\'')
            sql_d_unship = SQL_SHIPPING_SPEED % ('D', 'status <> \'SHIPPING\'')
            # 渐进
            sql_j_good = SQL_SHIPPING_SPEED % (
                'J', 'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) <= 2 AND status = \'SHIPPING\'')
            sql_j_average = SQL_SHIPPING_SPEED % ('J',
                                                  'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) > 2 AND TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) <= 5 AND status = \'SHIPPING\'')
            sql_j_poor = SQL_SHIPPING_SPEED % (
                'J', 'TIMESTAMPDIFF(DAY, DATE(create_at), DATE(update_at)) > 5 AND status = \'SHIPPING\'')
            sql_j_unship = SQL_SHIPPING_SPEED % ('J', 'status <> \'SHIPPING\'')

            cursor.execute(sql_d_good)
            res_d_good = namedtuplefetchall(cursor)
            cursor.execute(sql_d_average)
            res_d_average = namedtuplefetchall(cursor)
            cursor.execute(sql_d_poor)
            res_d_poor = namedtuplefetchall(cursor)
            cursor.execute(sql_d_unship)
            res_d_unship = namedtuplefetchall(cursor)

            cursor.execute(sql_j_good)
            res_j_good = namedtuplefetchall(cursor)
            cursor.execute(sql_j_average)
            res_j_average = namedtuplefetchall(cursor)
            cursor.execute(sql_j_poor)
            res_j_poor = namedtuplefetchall(cursor)
            cursor.execute(sql_j_unship)
            res_j_unship = namedtuplefetchall(cursor)

            return render(request, 'shipping_speed_report.html', {
                'res_d_good': res_d_good,
                'res_d_average': res_d_average,
                'res_d_poor': res_d_poor,
                'res_d_unship': res_d_unship,
                'res_j_good': res_j_good,
                'res_j_average': res_j_average,
                'res_j_poor': res_j_poor,
                'res_j_unship': res_j_unship,
            })

    except Exception as e:
        return HttpResponse(e.message)


# custom_tag
from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@login_required
@permission_required('report.CUSTOMIZE_REPORT', login_url='/oms/forbid/')
def redirect_customize_report(request):
    # 查询
    perm_prefix = 'report.CUSTOMIZE_REPORT'

    rm = response_message()
    _form_data = {}
    page_info = {}
    _form_data['request_module'] = 'Report'
    _form_data['request_feature'] = '自定义查询'
    _data = None

    # POST
    if request.method == 'POST':
        s_info = request.POST.get('info')
        s_page = request.POST.get('page', 1)
        cur_page = int(s_page)
        _data = json.loads(s_info)

        # 拼接SQL
        condition = []
        ext_parameters = '(%s)' % _data.get('parameters')
        start_date = _data.get('startDate', '2019.01.01')
        end_date = _data.get('endDate')

        customize_report_index = _data.get('customize_report_index', '-1')
        customize_report_code = _data.get('customize_report_code', '-1')
        logging.debug(customize_report_code)
        if customize_report_code == '-1':
            return HttpResponse("参数错误")

        crc = customize_report_controller()
        cr = crc.get_by_code(customize_report_code)

        # 查询
        try:
            if cr == None:
                rm.code = 404
                rm.message = '系统未能正确获取查询对象!'
                return render(request, 'customize_report_results.html', {
                    'form_data': _form_data,
                    'items': None,
                    'page_info': page_info,
                    'rm': rm,
                })

            perm = '%s_%s' % (perm_prefix, cr.group)
            user = request.user
            if not user.has_perm(perm):
                rm.code = 403
                rm.message = '该用户未获得当前操作的权限!'
                return render(request, 'customize_report_results.html', {
                    'form_data': _form_data,
                    'items': None,
                    'page_info': page_info,
                    'rm': rm,
                })

            with connections['pg_oms_query'].cursor() as cursor:

                sql = cr.sql_script

                logging.debug(ext_parameters)

                ext_parameters = ext_parameters.replace('|', ',')

                ext_parameters = tuple(eval(ext_parameters))
                logging.debug(ext_parameters)

                if cr.is_need_parameters:
                    sql = sql % ext_parameters

                logging.debug(sql)

                cursor.execute(sql)
                request.session['CUR_CUSTOMIZE_REPORT_NAME'] = cr.name
                request.session['CUR_CUSTOMIZE_SQL_SCRIPT'] = sql
                # results = namedtuplefetchall(cursor)
                results = dictfetchall(cursor)

                index = 0
                fields_index = []
                fields = []
                for ob in cursor.description:
                    logging.debug(ob[0])
                    fields.append(ob[0])
                    fields_index.append(index)
                    index += 1
                _form_data['fields'] = fields
                _form_data['fields_index'] = fields_index

                # logging.debug(results)

                # 分页
                page_data = Paginator(results, 100)
                page_info['cur_page'] = cur_page
                page_info['data_count'] = page_data.count
                page_info['page_count'] = page_data.num_pages
                page_info['prev_page'] = cur_page - 1
                page_info['next_page'] = cur_page + 1
                page_info['left_spnt'] = 0
                page_info['right_spnt'] = 0
                cur_page_data = page_data.page(cur_page)

                # 只显示show_page个页码
                show_page = 5
                half_count = (show_page - 1) / 2
                if page_data.num_pages > show_page:
                    if cur_page <= half_count + 1:
                        page_info['page_range'] = range(1, show_page + 1)
                        page_info['left_spnt'] = 0
                        page_info['right_spnt'] = 1
                    elif cur_page >= page_data.num_pages - half_count:
                        page_info['page_range'] = range(page_data.num_pages - show_page + 1, page_data.num_pages + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 0
                    else:
                        page_info['page_range'] = range(cur_page - half_count, cur_page + half_count + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 1
                else:
                    page_info['page_range'] = range(1, page_data.num_pages + 1)

                return render(request, 'customize_report_results.html', {
                    'form_data': _form_data,
                    'items': cur_page_data,
                    'page_info': page_info
                })

        except Exception as e:

            logging.debug(str(e))
            rm.code = -1
            rm.message = str(e)

            return render(request, 'customize_report_results.html', {
                'form_data': _form_data,
                'items': None,
                'page_info': page_info,
                'rm': rm,
            })

    # GET
    crc = customize_report_controller()
    customize_reports = crc.get_all()
    _form_data['customize_reports'] = customize_reports
    return render(request, 'customize_report.html', {
        'form_data': _form_data,
    })


@login_required
@permission_required('report.CUSTOMIZE_REPORT', login_url='/oms/forbid/')
def redirect_customize_report_csv(request):
    s_info = request.GET.get('info')
    sql = request.session['CUR_CUSTOMIZE_SQL_SCRIPT']
    try:
        cr_name = request.session['CUR_CUSTOMIZE_REPORT_NAME']
    except Exception as ex:
        cr_name = '来自高级自定义查询'
    logging.debug(sql)
    # 查询
    _form_data = {}
    try:
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            index = 0
            fields_index = []
            fields = []
            for ob in cursor.description:
                logging.debug(ob[0])
                fields.append(ob[0])
                fields_index.append(index)
                index += 1
            _form_data['fields'] = fields
            _form_data['fields_index'] = fields_index

            results = dictfetchall(cursor)
            response = HttpResponse(content_type='text/csv')
            file_name = 'customize_report_csv'
            response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
            response.write(codecs.BOM_UTF8)
            writer = csv.writer(response)
            writer.writerow([cr_name])
            writer.writerow([])
            writer.writerow(fields)
            for item in results:
                line = []
                for field in fields:
                    val = get_item(item, field)
                    line.append(val)
                writer.writerow(line)

            logging.debug('准备导出 ....')
            crc = customize_report_controller()
            data = {}
            data['name'] = cr_name
            data['event_type'] = 'EXPORT'
            data['sql_script'] = sql
            crc.log_query(request, data)

            logging.debug('记录完成')
            return response
    except Exception as e:
        return HttpResponse(str(e))


@login_required
@permission_required('report.CUSTOMIZE_REPORT', login_url='/oms/forbid/')
def redirect_customize_report_advanced(request):
    # 查询
    perm_prefix = 'report.CUSTOMIZE_REPORT'

    rm = response_message()
    _form_data = {}
    page_info = {}
    _form_data['request_module'] = 'Report'
    _form_data['request_feature'] = '高级自定义查询'
    _data = None

    user_id = request.user.id
    if user_id != 114 and user_id != 1 and user_id != 2 and user_id != 3:
        return HttpResponse('对不起, 你无此权限!')

    # POST
    if request.method == 'POST':
        s_info = request.POST.get('info')
        s_page = request.POST.get('page', 1)

        cur_page = int(s_page)
        _data = json.loads(s_info)
        sql_script = _data.get('parameters')
        sql_script = sql_script.replace('+', ' ')
        sql_script = sql_script.replace('%2C', ',')
        sql_script = sql_script.replace('%3D', '=')
        sql_script = sql_script.replace('%3B', '')
        sql_script = sql_script + ' limit 10000'
        # 查询
        try:

            with connections['pg_oms_query'].cursor() as cursor:

                sql = sql_script

                logging.debug(sql)
                cursor.execute(sql)
                request.session['CUR_CUSTOMIZE_SQL_SCRIPT'] = sql

                # results = namedtuplefetchall(cursor)
                results = dictfetchall(cursor)

                crc = customize_report_controller()
                data = {}
                data['event_type'] = 'QUERY'
                data['sql_script'] = sql
                crc.log_query(request, data)

                index = 0
                fields_index = []
                fields = []
                for ob in cursor.description:
                    logging.debug(ob[0])
                    fields.append(ob[0])
                    fields_index.append(index)
                    index += 1
                _form_data['fields'] = fields
                _form_data['fields_index'] = fields_index

                # logging.debug(results)

                # 分页
                page_data = Paginator(results, 100)
                page_info['cur_page'] = cur_page
                page_info['data_count'] = page_data.count
                page_info['page_count'] = page_data.num_pages
                page_info['prev_page'] = cur_page - 1
                page_info['next_page'] = cur_page + 1
                page_info['left_spnt'] = 0
                page_info['right_spnt'] = 0
                cur_page_data = page_data.page(cur_page)

                # 只显示show_page个页码
                show_page = 5
                half_count = (show_page - 1) / 2
                if page_data.num_pages > show_page:
                    if cur_page <= half_count + 1:
                        page_info['page_range'] = range(1, show_page + 1)
                        page_info['left_spnt'] = 0
                        page_info['right_spnt'] = 1
                    elif cur_page >= page_data.num_pages - half_count:
                        page_info['page_range'] = range(page_data.num_pages - show_page + 1, page_data.num_pages + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 0
                    else:
                        page_info['page_range'] = range(cur_page - half_count, cur_page + half_count + 1)
                        page_info['left_spnt'] = 1
                        page_info['right_spnt'] = 1
                else:
                    page_info['page_range'] = range(1, page_data.num_pages + 1)

                return render(request, 'customize_report_results.html', {
                    'form_data': _form_data,
                    'items': cur_page_data,
                    'page_info': page_info
                })

        except Exception as e:

            logging.debug(str(e))
            rm.code = -1
            rm.message = str(e)

            return render(request, 'customize_report_results.html', {
                'form_data': _form_data,
                'items': None,
                'page_info': page_info,
                'rm': rm,
            })

    # GET
    crc = customize_report_controller()
    customize_reports = crc.get_all()
    _form_data['customize_reports'] = customize_reports
    return render(request, 'customize_report_advanced.html', {
        'form_data': _form_data,
    })


@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_shipping_speed_report_new(request):
    """出货速度统计报表"""
    try:
        _form_data = {}  # 回传参数
        rm = response_message()
        page = request.GET.get('page', 1)
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(SQL_SHIPPING_SPEED_REPORT_NEW)
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
            return render(request, 'shipping_speed_report_new.html', {
                'form_data': _form_data,
                'list': _items,
                'response_message': rm,
                'requestUrl': reverse('report_shipping_speed_report_new'),
                'query_string': query_string,
                'paginator': paginator,
            })

    except Exception as e:
        logging.debug(e)
        return HttpResponse(e.message)


@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_save_shipping_speed_report_csv(request):
    """保存shipping_speed_reportcsv"""
    try:
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(SQL_SHIPPING_SPEED_REPORT_NEW)
            _items = dictfetchall(cursor)
            response = HttpResponse(content_type='text/csv')
            fieldnames = ['lab_number', 'status', 'ship_direction', 'vendor', 'tint_sku',
                          'shipping_id', 'created_at', 'shipped_date', 'ship_diff', 'shipped_diff_level', 'quantity']
            file_name = 'shipping_speed_report'
            response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
            response.write(codecs.BOM_UTF8)
            writer = csv.writer(response)
            writer.writerow(fieldnames)
            for item in _items:
                line = []
                for field in fieldnames:
                    val = get_item(item, field)
                    line.append(val)
                writer.writerow(line)
            return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e.message)


@login_required
@permission_required('report.DALIY_REPORT', login_url='/oms/forbid/')
def daliy_production_report(request):
    "生产日报表"
    day = request.GET.get('day', '')
    if day == '':
        td = datetime.datetime.now()
        day = td.strftime('%Y-%m-%d')
        days = "date(\'%s\')" % (day)
        logging.debug(day)
    if not day == '':
        days = "date(\'%s\')" % (day)
        logging.debug(day)
    try:
        _form_data = {}  # 回传参数
        rm = response_message()
        page = request.GET.get('page', 1)
        with connections['pg_oms_query'].cursor() as cursor:
            sql = SQL_PRODUCTION_REPORT % (days, days, days, days, days, days, days)
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)
        with connections['pg_oms_query'].cursor() as detailcursor:
            detail_sql = SQL_PRODUCTION_DETAIL_REPORT % (days)
            detailcursor.execute(detail_sql)
            _detail_items = namedtuplefetchall(detailcursor)

        new_dics = {}
        new_lists = []

        # 取出vd2+4+7+8 dy,vd5+6+9+10 sh
        dy_all_order = 0
        dy_true_order = 0
        dy_unable_order = 0
        dy_reset_order = 0

        dy_customer_order = 0
        dy_to_order = 0

        sh_all_order = 0
        sh_true_order = 0
        sh_unable_order = 0
        sh_reset_order = 0
        sh_customer_order = 0
        sh_to_order = 0
        for item in _detail_items:
            if item.vendor == '2' or item.vendor == '4' or item.vendor == '7' or item.vendor == '8':
                dy_all_order += item.all_order
                dy_true_order += item.true_order
                dy_unable_order += item.unable_order
                dy_reset_order += item.reset_order
                dy_customer_order += item.customer_order
                dy_to_order += item.to_order
            if item.vendor == '5' or item.vendor == '6' or item.vendor == '9' or item.vendor == '10':
                sh_all_order += item.all_order
                sh_true_order += item.true_order
                sh_unable_order += item.unable_order
                sh_reset_order += item.reset_order
                sh_customer_order += item.customer_order
                sh_to_order += item.to_order

        new_dics['dy_all_order'] = dy_all_order
        new_dics['dy_true_order'] = dy_true_order
        new_dics['dy_unable_order'] = dy_unable_order
        new_dics['dy_reset_order'] = dy_reset_order
        new_dics['dy_customer_order'] = dy_customer_order
        new_dics['dy_to_order'] = dy_to_order

        new_dics['sh_all_order'] = sh_all_order
        new_dics['sh_true_order'] = sh_true_order
        new_dics['sh_unable_order'] = sh_unable_order
        new_dics['sh_reset_order'] = sh_reset_order
        new_dics['sh_customer_order'] = sh_customer_order
        new_dics['sh_to_order'] = sh_to_order

        new_lists.append(new_dics)
        print(new_lists)
        logging.debug("--------------------")

        return render(request, 'daliy_production_report.html', {
            'form_data': _form_data,
            'list': _items,
            'detail_list': _detail_items,
            'factory_list': new_lists,
            'response_message': rm,
            'requestUrl': reverse('daliy_production_report'),
            'day': day
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e.message)


def last_day_of_month(any_day):
    """
    获取获得一个月中的最后一天
    :param any_day: 任意日期
    :return: string
    """
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)


@login_required
@permission_required('report.PGORDER_REPORT', login_url='/oms/forbid/')
def redirect_pg_order_report_csv(request):
    # 查询
    form_data = {}
    new_lists = []
    now_year = datetime.datetime.now().year
    # 获取每个月得最后一天
    now_1 = str(now_year) + u'-01'
    now_1_30 = last_day_of_month(datetime.date(now_year, 1, 1))

    # 获取每个月第一天
    now_first = str(now_year) + u'-01' + u'-01'
    sum_sql = """
    (select count(t0.id) as sum,'%s' AS `month` from oms_pgorder t0 where 1=1
            and customer_id <> '' and date(create_at)>= date('%s') AND date(create_at)<= date('%s')
             and t0.status <>'CANCELED')
    """ % (now_1, now_first, now_1_30)
    new_sql = """
    (select coalesce(sum(counts),0) as sum,'%s' AS `month` from (select customer_id,count(1) as counts from oms_pgorder  where
date(create_at)>= date('%s') AND date(create_at)<= date('%s')
GROUP BY customer_id having count(1)>1) t0)
    """ % (now_1, now_first, now_1_30)
    replace_sql = """
    (SELECT COUNT(id) AS sum,'%s' AS `month`  FROM oms_pgorder t0 WHERE 
    DATE(t0.create_at)>= DATE('%s')
 AND DATE(t0.create_at)<= DATE('%s') 
AND t0.coupon_code LIKE 'REPLACE%%')
    """ % (now_1, now_first, now_1_30)
    history_sql = """(SELECT COUNT(t0.id) AS sum,'%s' AS `month` FROM oms_pgorder t0 WHERE 1=1
AND DATE(t0.create_at)>= DATE('%s') 
AND DATE(t0.create_at)<= DATE('%s') 
AND t0.customer_id IN (SELECT t9.customer_id FROM oms_pgorder t9 WHERE 1=1 
AND DATE(t9.create_at)< DATE('%s')))""" % (now_1, now_first, now_1_30, now_first)
    cancle_sql = """(SELECT '%s' AS `month`, count(t0.id) as sum
        from oms_pgorder t0
        where
        date(create_at) >= date('%s')
        AND
        date(create_at) <= date('%s')
        and t0.status = 'CANCELED')""" % (now_1, now_first, now_1_30)
    for month in range(2, 13):
        last_day = last_day_of_month(datetime.date(now_year, month, 1))
        now_2 = str(now_year) + u'-' + str(month)
        now_first = str(now_year) + u'-' + str(month) + u'-01'
        cancle_sql += """UNION
    (SELECT '%s' AS `month`,count(t0.id) as sum from oms_pgorder t0 where
    date(create_at)>= date('%s') AND date(create_at)<= date('%s')
    and t0.status = 'CANCELED')""" % (now_2, now_first, last_day)
        history_sql += """UNION
            (SELECT COUNT(t0.id) AS sum,'%s' AS `month` FROM oms_pgorder t0 WHERE 1=1 
AND DATE(t0.create_at)>= DATE('%s') 
AND DATE(t0.create_at)<= DATE('%s') 
AND t0.customer_id IN (SELECT t9.customer_id FROM oms_pgorder t9 WHERE 1=1 
AND DATE(t9.create_at)< DATE('%s')))""" % (now_2, now_first, last_day, now_first)
        replace_sql += """UNION
            (SELECT COUNT(id) AS sum,'%s' AS `month`  FROM oms_pgorder t0 WHERE 
    DATE(t0.create_at)>= DATE('%s')
 AND DATE(t0.create_at)<= DATE('%s') 
AND t0.coupon_code LIKE 'REPLACE%%')""" % (now_2, now_first, last_day)
        new_sql += """UNION
            (select coalesce(sum(counts),0) as sum,'%s' AS `month` from (select customer_id,count(1) as counts from oms_pgorder  where
date(create_at)>= date('%s') AND date(create_at)<= date('%s')
GROUP BY customer_id having count(1)>1) t0)
            """ % (now_2, now_first, last_day)
        sum_sql += """UNION
            (select count(t0.id) as sum,'%s' AS `month` from oms_pgorder t0 where 1=1
            and customer_id <> '' and date(create_at)>= date('%s') AND date(create_at)<= date('%s')
             and t0.status <>'CANCELED')
            """ % (now_2, now_first, last_day)

    try:
        with connections['default'].cursor() as cursor:
            # 历史单
            cursor.execute(cancle_sql)
            new_lists_cancle = namedtuplefetchall(cursor)
            cursor.execute(history_sql)
            new_lists_history = namedtuplefetchall(cursor)
            cursor.execute(replace_sql)
            new_lists_replace = namedtuplefetchall(cursor)
            cursor.execute(new_sql)
            new_lists_new = namedtuplefetchall(cursor)
            cursor.execute(sum_sql)
            sum_lists_new = namedtuplefetchall(cursor)

            sum1 = sum_lists_new[0].sum
            sum2 = sum_lists_new[1].sum
            sum3 = sum_lists_new[2].sum
            sum4 = sum_lists_new[3].sum
            sum5 = sum_lists_new[4].sum
            sum6 = sum_lists_new[5].sum
            sum7 = sum_lists_new[6].sum
            sum8 = sum_lists_new[7].sum
            sum9 = sum_lists_new[8].sum
            sum10 = sum_lists_new[9].sum
            sum11 = sum_lists_new[10].sum
            sum12 = sum_lists_new[11].sum

            new1 = new_lists_new[0].sum
            new2 = new_lists_new[1].sum
            new3 = new_lists_new[2].sum
            new4 = new_lists_new[3].sum
            new5 = new_lists_new[4].sum
            new6 = new_lists_new[5].sum
            new7 = new_lists_new[6].sum
            new8 = new_lists_new[7].sum
            new9 = new_lists_new[8].sum
            new10 = new_lists_new[9].sum
            new11 = new_lists_new[10].sum
            new12 = new_lists_new[11].sum

            history1 = new_lists_history[0].sum
            history2 = new_lists_history[1].sum
            history3 = new_lists_history[2].sum
            history4 = new_lists_history[3].sum
            history5 = new_lists_history[4].sum
            history6 = new_lists_history[5].sum
            history7 = new_lists_history[6].sum
            history8 = new_lists_history[7].sum
            history9 = new_lists_history[8].sum
            history10 = new_lists_history[9].sum
            history11 = new_lists_history[10].sum
            history12 = new_lists_history[11].sum

            form_data['sum'] = sum1 - (new1 + history1)
            form_data['month'] = now_1
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum2 - (new2 + history2)
            form_data['month'] = str(now_year) + u'-02'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum3 - (new3 + history3)
            form_data['month'] = str(now_year) + u'-03'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum4 - (new4 + history4)
            form_data['month'] = str(now_year) + u'-04'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum5 - (new5 + history5)
            form_data['month'] = str(now_year) + u'-05'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum6 - (new6 + history6)
            form_data['month'] = str(now_year) + u'-06'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum7 - (new7 + history7)
            form_data['month'] = str(now_year) + u'-07'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum8 - (new8 + history8)
            form_data['month'] = str(now_year) + u'-08'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum9 - (new9 + history9)
            form_data['month'] = str(now_year) + u'-09'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum10 - (new10 + history10)
            form_data['month'] = str(now_year) + u'-10'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum11 - (new11 + history11)
            form_data['month'] = str(now_year) + u'-11'
            new_lists.append(form_data)
            form_data = {}
            form_data['sum'] = sum12 - (new12 + history12)
            form_data['month'] = str(now_year) + u'-12'
            new_lists.append(form_data)
            form_data = {}

            return render(request, 'pg_order_report.html', {
                'new_lists_new': new_lists,
                'new_lists_history': new_lists_history,
                'new_lists_replace': new_lists_replace,
                'new_lists_cancle': new_lists_cancle,
                'requestUrl': reverse('pg_order_report')
            })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
@permission_required('report.DALIY_RETURN_REPORT', login_url='/oms/forbid/')
def daliy_production_return_report(request):
    "生产报损统计"
    day = request.GET.get('day', '')
    v5 = 0
    if day == '':
        td = datetime.datetime.now()
        day = td.strftime('%Y-%m-%d')
        days = "date(\'%s\')" % (day)

    if not day == '':
        days = "date(\'%s\')" % (day)

    try:
        items = []
        _form_data = {}  # 回传参数
        rm = response_message()
        page = request.GET.get('page', 1)
        with connections['pg_oms_query'].cursor() as cursor:
            sql = SQL_PRODUCTION_RETURN_REPORT % (days)
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)
        with connections['pg_oms_query'].cursor() as detailcursor:
            detail_sql = SQL_PRODUCTION_DETAIL_REPORT % (days)
            detailcursor.execute(detail_sql)
            _detail_items = namedtuplefetchall(detailcursor)

        new_dics = {}
        new_lists = []
        ws_lists = []
        v0_all_order = 0
        v1_all_order = 0
        v2_all_order = 0
        v4_all_order = 0
        v5_all_order = 0
        v6_all_order = 0
        v7_all_order = 0
        v8_all_order = 0
        v9_all_order = 0
        v10_all_order = 0
        v1000_all_order = 0

        v0_return_order = 0
        v1_return_order = 0
        v2_return_order = 0
        v4_return_order = 0
        v5_return_order = 0
        v6_return_order = 0
        v7_return_order = 0
        v8_return_order = 0
        v9_return_order = 0
        v10_return_order = 0
        v1000_return_order = 0

        vendor = ''
        for item in _detail_items:
            if item.vendor == '0':
                v0_all_order += item.all_order
            if item.vendor == '1':
                v1_all_order += item.all_order
            if item.vendor == '2':
                v2_all_order += item.all_order
            if item.vendor == '4':
                v4_all_order += item.all_order
            if item.vendor == '5':
                v5_all_order += item.all_order
            if item.vendor == '6':
                v6_all_order += item.all_order
            if item.vendor == '7':
                v7_all_order += item.all_order
            if item.vendor == '8':
                v8_all_order += item.all_order
            if item.vendor == '9':
                v9_all_order += item.all_order
            if item.vendor == '10':
                v10_all_order += item.all_order
            if item.vendor == '1000':
                v1000_all_order += item.all_order

        for return_item in _items:
            if return_item.vendor == '0':
                v0_return_order += return_item.return_order
                new_dics['vendor'] = 'VD0'
                new_dics['all_order'] = v0_all_order
                new_dics['return_order'] = v0_return_order
                vendor = '0'
            if return_item.vendor == '1':
                v1_return_order += return_item.return_order
                new_dics['vendor'] = 'VD1'
                new_dics['all_order'] = v1_all_order
                new_dics['return_order'] = v1_return_order
                vendor = '1'
            if return_item.vendor == '2':
                v2_return_order += return_item.return_order
                new_dics['vendor'] = 'VD2'
                new_dics['all_order'] = v2_all_order
                new_dics['return_order'] = v2_return_order
                vendor = '2'
            if return_item.vendor == '4':
                v4_return_order += return_item.return_order
                new_dics['vendor'] = 'VD4'
                new_dics['all_order'] = v4_all_order
                new_dics['return_order'] = v4_return_order
                vendor = '4'
            if return_item.vendor == '5':
                v5_return_order += return_item.return_order
                new_dics['vendor'] = 'VD5'
                new_dics['all_order'] = v5_all_order
                new_dics['return_order'] = v5_return_order
                vendor = '5'
            if return_item.vendor == '6':
                v6_return_order += return_item.return_order
                new_dics['vendor'] = 'VD6'
                new_dics['all_order'] = v6_all_order
                new_dics['return_order'] = v6_return_order
                vendor = '6'
            if return_item.vendor == '7':
                v7_return_order += return_item.return_order
                new_dics['vendor'] = 'VD7'
                new_dics['all_order'] = v7_all_order
                new_dics['return_order'] = v7_return_order
                vendor = '7'
            if return_item.vendor == '8':
                v8_return_order += return_item.return_order
                new_dics['vendor'] = 'VD8'
                new_dics['all_order'] = v8_all_order
                new_dics['return_order'] = v8_return_order
                vendor = '8'
            if return_item.vendor == '9':
                v9_return_order += return_item.return_order
                new_dics['vendor'] = 'VD9'
                new_dics['all_order'] = v9_all_order
                new_dics['return_order'] = v9_return_order
                vendor = '9'
            if return_item.vendor == '10':
                v10_return_order += return_item.return_order
                new_dics['vendor'] = 'VD10'
                new_dics['all_order'] = v10_all_order
                new_dics['return_order'] = v10_return_order
                vendor = '10'
            if return_item.vendor == '1000':
                v1000_return_order += return_item.return_order
                new_dics['vendor'] = 'VD1000'
                new_dics['all_order'] = v1000_all_order
                new_dics['return_order'] = v1000_return_order
                vendor = '1000'
            if vendor <> '':
                with connections['pg_oms_query'].cursor() as wscursor:
                    ws_sql = SQL_GLASS_RETURN_REPORT % (days, vendor)
                    wscursor.execute(ws_sql)
                    ws_items = namedtuplefetchall(wscursor)
                    ws_lists = ws_items
            if vendor <> '':
                new_dics['ws_list'] = ws_lists
                new_lists.append(new_dics)
                new_dics = {}

        return render(request, 'daliy_production_return_report.html', {
            'form_data': _form_data,
            'response_message': rm,
            'list': new_lists,
            'requestUrl': reverse('daliy_production_return_report'),
            'day': day
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
@permission_required('report.PGORDER_APPROVE_PROCESSING_REPORT', login_url='/oms/forbid/')
def pgorder_approve_processing_report(request):
    "审单耗时统计"
    day = request.GET.get('day', '')
    day_tmp = day
    _form_data = {}
    page = request.GET.get('page', 1)
    report_year = ''
    report_month = ''
    report_day = ''
    if day_tmp == '':
        td = datetime.datetime.now()
        day = td.strftime('%Y-%m-%d')
        report_year = datetime.datetime.now().year
        report_month = datetime.datetime.now().month
        report_day = datetime.datetime.now().day
    if not day_tmp == '':
        dt = datetime.datetime.strptime(day_tmp, '%Y-%m-%d')
        report_year = dt.year
        report_month = dt.month
        report_day = dt.day

    try:
        pgorder_report = PgOrderProcessingReport.objects.filter(report_year=report_year, report_month=report_month,
                                                                report_day=report_day)
        _items = pgorder_report.order_by('created_at')
        _form_data['total'] = _items.count()

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'pgorder_approve_processing_report.html', {
            'form_data': '',
            'list': _items,
            'requestUrl': reverse('pgorder_approve_processing_report'),
            'day': day,
            'query_string': query_string,
            'paginator': paginator,
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def pgorder_approve_processing_report_generate(request):
    "审单耗时统计报表生成"
    _form_data = {}
    res = {}
    form_data = request.POST.get("form_data")
    try:
        _data = json.loads(form_data)
        start_date = _data.get('start_date')
        end_date = _data.get('end_date')
        logging.debug(start_date)
        logging.debug(end_date)
        pgc = PgOrderProcessingReportController()
        rm = pgc.generate_pgorder_report_bydate(start_date, end_date)

        res['code'] = rm.code
        res['message'] = rm.message

    except Exception as e:
        res['code'] = -999
        res['message'] = '数据遇到异常: ' + e.message

    return HttpResponse(json.dumps(res))


@login_required
@permission_required('report.LABORDER_PRODUCTION_REPORT', login_url='/oms/forbid/')
def laborder_production_report(request):
    "订单耗时统计"
    day = request.GET.get('day', '')
    day_tmp = day
    _form_data = {}
    page = request.GET.get('page', 1)
    report_year = ''
    report_month = ''
    report_day = ''
    if day_tmp == '':
        td = datetime.datetime.now()
        day = td.strftime('%Y-%m-%d')
        report_year = datetime.datetime.now().year
        report_month = datetime.datetime.now().month
        report_day = datetime.datetime.now().day
    if not day_tmp == '':
        dt = datetime.datetime.strptime(day_tmp, '%Y-%m-%d')
        report_year = dt.year
        report_month = dt.month
        report_day = dt.day

    try:

        pgorder_report = LabOrderProductionReport.objects.filter(report_year=report_year, report_month=report_month,
                                                                 report_day=report_day)
        _items = pgorder_report.order_by('created_at')
        _form_data['total'] = _items.count()

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'laborder_production_report.html', {
            'form_data': '',
            'list': _items,
            'requestUrl': reverse('laborder_production_report'),
            'day': day,
            'query_string': query_string,
            'paginator': paginator,
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
@permission_required('report.LABORDER_FLOW_REPORT', login_url='/oms/forbid/')
def laborder_flow_report(request):
    "订单耗时统计"
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    vendor = request.GET.get('vendor', 'all')
    ship = request.GET.get('ship', 'all')
    lens_type = request.GET.get('lens_type', 'all')
    _form_data = {}
    page = request.GET.get('page', 1)


    try:
        # 发货方式列表
        SHIP_DIRECTION_CHOICES = LabOrder.SHIP_DIRECTION_CHOICES
        ship_direction_list = []
        for dir in SHIP_DIRECTION_CHOICES:
            sc = status_choice()
            sc.key = dir[0]
            sc.value = dir[1]
            ship_direction_list.append(sc)

        # VD列表
        vendors_choice_list = []
        for vcl in LabOrder.VENDOR_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            vendors_choice_list.append(vc)
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql= SQL_FLOW_REPORT %(end_date, start_date, end_date)
                if vendor != '' and vendor != 'all':
                    sql = sql + """ AND t0.vendor='%s'""" % vendor

                if ship != '' and ship != 'all':
                    sql = sql + """ AND t0.act_ship_direction='%s'""" % ship

                if lens_type != '' and lens_type != 'all':
                    if lens_type == 'C':
                        l_type = True
                    else:
                        l_type = False

                    sql = sql + """ AND t3.is_rx_lab=%s """ % l_type
                print(sql)
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)

        _form_data['total'] = len(_items)

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'laborder_flow_report.html', {
            'form_data': _form_data,
            'list': _items,
            'vendors_choices': vendors_choice_list,
            'ship_choices': ship_direction_list,
            'requestUrl': reverse('report_laborder_flow_report'),
            'start_date': start_date,
            'end_date': end_date,
            'vendor': vendor,
            'ship': ship,
            'lens_type': lens_type,
            'query_string': query_string,
            'paginator': paginator
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
@permission_required('report.LABORDER_FLOW_REPORT', login_url='/oms/forbid/')
def laborder_flow_report_csv(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    vendor = request.GET.get('vendor', 'all')
    ship = request.GET.get('ship', 'all')
    lens_type = request.GET.get('lens_type', 'all')
    _form_data = {}
    page = request.GET.get('page', 1)
    try:
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql= SQL_FLOW_REPORT %(end_date, start_date, end_date)
                if vendor != '' and vendor != 'all':
                    sql = sql + """ AND t0.vendor='%s'""" % vendor

                if ship != '' and ship != 'all':
                    sql = sql + """ AND t0.act_ship_direction='%s'""" % ship

                if lens_type != '' and lens_type != 'all':
                    if lens_type == 'C':
                        l_type = True
                    else:
                        l_type = False

                    sql = sql + """ AND t3.is_rx_lab=%s """ % l_type
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)
        import csv, codecs

        response = HttpResponse(content_type='text/csv')
        file_name = 'laborder_flow_report'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '工厂订单号', '状态','发货方式', 'Vendor', 'Workshop', '镜架',
            '框型', '数量', '镜片', '高散', '染色', '镜片类型', '订单日期',
            'lab订单生成时间', 'lab订单更新时间', '生产天数', 'lab订单预计完成', '待装配时间', 'lab生成到待装配时间差', '预发货时间',
            'lab生成到预发货时间差'
        ])

        for item in _items:
            writer.writerow([
                item.lab_number, item.status, item.act_ship_direction, item.vendor, item.workshop, item.frame,
                item.frame_type, item.quantity, item.act_lens_name, item.is_cyl_high,item.tint_name, item.lens_type, item.order_date,
                item.lab_create_at, item.lab_update_at, item.days_of_production, item.lab_estimated_date, item.ready_created_at, item.diff_ready_hour,
                item.pre_created_at,item.diff_pre_hour
            ])

        return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def shipment_pc_lens_lab_report(request):
    "订单耗时统计"
    start_date = request.GET.get('start_date', '')
    _form_data = {}
    page = request.GET.get('page', 1)


    try:
        with connections['pg_oms_query'].cursor() as cursor:
            sql= """SELECT DATE(t0.created_at) as created_at, COUNT(1) as cnt FROM
                        shipment_pre_delivery_line AS t0
                        LEFT JOIN oms_laborder AS t1 
                        ON t0.lab_order_entity_id = t1.id
                    WHERE t1.act_lens_sku LIKE "%%%s%%" 
            """ % '59'
            if start_date != '':
                sql = sql + """ AND DATE(t0.created_at)='%s' """ % start_date
            sql = sql + """ GROUP BY DATE(t0.created_at) ORDER BY t0.created_at DESC"""
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)

        _form_data['total'] = len(_items)

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'shipment_pc_lab_report.html', {
            'form_data': _form_data,
            'list': _items,
            'requestUrl': reverse('report_shipment_pc_lens_lab_report'),
            'query_string': query_string,
            'paginator': paginator
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def shipment_pc_lens_lab_line(request):
    date = request.GET.get('date', '')
    _form_data = {}
    page = request.GET.get('page', 1)

    try:
        with connections['pg_oms_query'].cursor() as cursor:
            sql= """SELECT t1.lab_number,
                           t1.act_ship_direction,
                           t1.vendor,
                           t1.act_lens_name,
                           t1.act_lens_sku,
                           t1.status,
                           t1.create_at as lab_create_at, 
                           t0.created_at AS ship_create_at
                    FROM shipment_pre_delivery_line AS t0 
                         LEFT JOIN oms_laborder AS t1 
                         ON t0.lab_order_entity_id = t1.id 
                         WHERE t1.act_lens_sku  LIKE '%%%s%%' 
                         AND DATE(t0.created_at)='%s'
            """ % ('59', date)
            print(sql)
            cursor.execute(sql)
            _items = namedtuplefetchall(cursor)

        _form_data['total'] = len(_items)

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'shipment_pc_lab_report_line.html', {
            'form_data': _form_data,
            'list': _items,
            'requestUrl': reverse('report_shipment_pc_lens_lab_line'),
            'query_string': query_string,
            'paginator': paginator
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def pgorder_coupon_report(request):
    "订单耗时统计"
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    _form_data = {}
    page = request.GET.get('page', 1)
    try:
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql = SQL_PGORDER_COUPON_REPORT % (end_date, start_date, end_date)
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)

        _form_data['total'] = len(_items)

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'pgorder_cop_report.html', {
            'form_data': _form_data,
            'list': _items,
            'requestUrl': reverse('report_pgorder_coupon_report'),
            'start_date': start_date,
            'end_date': end_date,
            'query_string': query_string,
            'paginator': paginator
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def pgorder_coupon_report_csv(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    _form_data = {}
    page = request.GET.get('page', 1)
    try:
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql = SQL_PGORDER_COUPON_REPORT % (end_date, start_date, end_date)
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)
        import csv, codecs

        response = HttpResponse(content_type='text/csv')
        file_name = 'pgorder_coupon_report'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            'Order Number', 'Lab Number','Coupon Code', 'Warranty', 'Create Date'
        ])

        for item in _items:
            writer.writerow([
                item.order_number, item.lab_number, item.coupon_code, item.warranty, item.create_at
            ])

        return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)



@login_required
@permission_required('report.LENS_REPORT', login_url='/oms/forbid/')
def redirect_web_order_report_v3(request):
    rm = response_message()
    message = None
    data_list = []
    last_day = ''
    try:
        filter_day = request.GET.get("filter_day", "")
        if filter_day:
            for i in range(int(filter_day)):
                t_day = (datetime.datetime.now() + datetime.timedelta(days=~int(i))).strftime("%Y-%m-%d")
                item = {}
                item['report_day'] = t_day
                item['web_order'] = 0
                item['undisposed'] = 0
                item['web_glasses_qty'] = 0
                item['lad_order'] = 0
                item['lens_receive'] = 0
                item['glasses_recive'] = 0
                item['picking'] = 0
                item['picking_pct'] = 0
                data_list.append(item)
                if i == int(filter_day) -1:
                    last_day = t_day

            with connections['pg_oms_query'].cursor() as cursor:
                sql ="""SELECT date(convert_tz(t0.create_at ,@@SESSION .time_zone,'+8:00')) AS create_at, count(t0.id) AS web_order 
                        FROM oms_pgorder t0 where date(create_at)>='%s' GROUP BY DATE(create_at) ORDER BY DATE(create_at) DESC """ % last_day
                cursor.execute(sql)
                web_order_dict = {}
                for item in namedtuplefetchall(cursor):
                    web_order_dict[item.create_at.strftime("%Y-%m-%d")] = item.web_order

                undisposed_sql ="""SELECT date(convert_tz(t0.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, count(t0.id) AS undisposed
                                   FROM oms_pgorder t0 WHERE DATE(create_at) >='%s' and t0.is_inlab=False GROUP BY DATE(create_at) ORDER BY DATE(create_at) DESC """ % last_day
                cursor.execute(undisposed_sql)
                undisposed_dict = {}
                for item in namedtuplefetchall(cursor):
                    undisposed_dict[item.create_at.strftime("%Y-%m-%d")] = item.undisposed

                web_glasses_sql ="""SELECT date(convert_tz(t0.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, sum(t0.quantity) AS web_glasses_qty 
                                    FROM oms_pgorderitem t0 WHERE DATE(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))>='%s' GROUP BY DATE(create_at) ORDER BY DATE(create_at) DESC """ % last_day
                cursor.execute(web_glasses_sql)
                web_glasses_dict = {}
                for item in namedtuplefetchall(cursor):
                    web_glasses_dict[item.create_at.strftime("%Y-%m-%d")] = item.web_glasses_qty

                lad_order_sql = """SELECT date(convert_tz(t1.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, count(t0.id) AS lad_order 
                             FROM oms_laborder AS t0 LEFT JOIN oms_pgorder AS t1 ON t0.order_number=t1.order_number 
                             WHERE date(convert_tz(t1.create_at,@@session.time_zone,'+8:00')) >='%s'  
                                        AND t0.is_enabled=True AND t0.status<>'CANCELED' GROUP BY date(convert_tz(t1.create_at,@@session.time_zone,'+8:00')) 
                                  ORDER BY date(convert_tz(t1.create_at,@@session.time_zone,'+8:00')) DESC""" % last_day

                cursor.execute(lad_order_sql)
                lad_order_dict = {}
                for item in namedtuplefetchall(cursor):
                    lad_order_dict[item.create_at.strftime("%Y-%m-%d")] = item.lad_order

                lens_receive_sql = """SELECT COUNT(DISTINCT t3.lab_number) AS order_count, t3.create_at as create_at FROM 
                                                (SELECT date(convert_tz(t1.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, t0.order_number, 
                                                        t0.lab_number,t0.status,t0.is_enabled,t0.id FROM oms_pgorder t1 
                                                        LEFT JOIN oms_laborder AS t0 ON t1.order_number = t0.order_number 
                                                 WHERE date(convert_tz(t1.create_at ,@@SESSION .time_zone,'+8:00')) >= '%s') AS t3 
                                        LEFT JOIN qc_lens_collection AS t4 ON t3.id=t4.laborder_id 
                                        WHERE t3.is_enabled=True AND t3.status<>'CANCELED' AND t4.id<>'' 
                                        GROUP BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) 
                                        ORDER BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) DESC """ % last_day

                cursor.execute(lens_receive_sql)
                lens_receive_dict = {}
                for item in namedtuplefetchall(cursor):
                    lens_receive_dict[item.create_at.strftime("%Y-%m-%d")] = item.order_count

                glasses_recive_sql = """ SELECT COUNT(DISTINCT t3.lab_number) AS glasses_recive, t3.create_at as create_at FROM 
                                                (SELECT date(convert_tz(t1.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, t0.order_number, 
                                                        t0.lab_number,t0.status,t0.is_enabled,t0.id FROM oms_pgorder t1 
                                                        LEFT JOIN oms_laborder AS t0 ON t1.order_number = t0.order_number 
                                                 WHERE date(convert_tz(t1.create_at ,@@SESSION .time_zone,'+8:00')) >= '%s') AS t3 
                                        LEFT JOIN oms_received_glasses AS t4 ON t3.id=t4.lab_order_entity 
                                        WHERE t3.is_enabled=True AND t3.status<>'CANCELED' AND t4.id<>'' 
                                        GROUP BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) 
                                        ORDER BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) DESC""" % last_day

                cursor.execute(glasses_recive_sql)
                glasses_recive_dict = {}
                for item in namedtuplefetchall(cursor):
                    glasses_recive_dict[item.create_at.strftime("%Y-%m-%d")] = item.glasses_recive

                picking_sql = """ SELECT COUNT(DISTINCT t3.lab_number) AS order_count, t3.create_at as create_at FROM 
                                                (SELECT date(convert_tz(t1.create_at ,@@SESSION .time_zone, '+8:00')) AS create_at, t0.order_number, 
                                                        t0.lab_number,t0.status,t0.is_enabled,t0.id FROM oms_pgorder t1 
                                                        LEFT JOIN oms_laborder AS t0 ON t1.order_number = t0.order_number 
                                                 WHERE date(convert_tz(t1.create_at ,@@SESSION .time_zone,'+8:00')) >= '%s') AS t3 
                                        LEFT JOIN shipment_pre_delivery_line AS t4 ON t3.id=t4.lab_order_entity_id 
                                        WHERE t3.is_enabled=True AND t3.status<>'CANCELED' AND t4.id<>'' 
                                        GROUP BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) 
                                        ORDER BY date(convert_tz(t3.create_at,@@session.time_zone,'+8:00')) DESC""" % last_day

                cursor.execute(picking_sql)
                picking_dict = {}
                for item in namedtuplefetchall(cursor):
                    picking_dict[item.create_at.strftime("%Y-%m-%d")] = item.order_count
            print(web_order_dict)
            for data_item in data_list:
                web_glasses_qty = web_glasses_dict.get(data_item['report_day'], 0)
                picking_qty = picking_dict.get(data_item['report_day'], 0)
                data_item['web_order'] = web_order_dict.get(data_item['report_day'], 0)
                data_item['undisposed'] = undisposed_dict.get(data_item['report_day'], 0)
                data_item['web_glasses_qty'] = web_glasses_dict.get(data_item['report_day'], 0)
                data_item['lad_order'] = lad_order_dict.get(data_item['report_day'], 0)
                data_item['lens_receive'] = lens_receive_dict.get(data_item['report_day'], 0)
                data_item['glasses_recive'] = glasses_recive_dict.get(data_item['report_day'], 0)
                data_item['picking'] = picking_qty
                rate = '-'
                if web_glasses_qty:
                    fl_web_glasses_qty = float(web_glasses_qty)
                    fl_picking = float(picking_qty)
                    if fl_web_glasses_qty > 0:
                        rate = fl_picking / fl_web_glasses_qty
                        rate = '%.2f%%' % (rate * 100)
                data_item['picking_pct'] = rate

        return render(request, 'web_order_report_new.html',
                      {
                        "data_list": data_list
                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)

def redirect_report_purchase_order_time_report(request):
    v24_data_dict = collections.OrderedDict()
    v30_data_dict = collections.OrderedDict()
    v48_data_dict = collections.OrderedDict()
    v72_data_dict = collections.OrderedDict()
    purchase_dict = {}
    v24_total = 0
    v30_total = 0
    v48_total = 0
    v72_total = 0
    data_set = set()
    try:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        vendor = request.GET.get('vendor', '')
        if start_date != '' and end_date != '':
            if vendor == '9':
                sql = VD9_PURCHASE_DIFF_SQL % (end_date, start_date, end_date)
            else:
                sql = VD4_PURCHASE_DIFF_SQL % (end_date, start_date, end_date)

            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)

                for item in namedtuplefetchall(cursor):
                    if item.lab_number not in data_set:
                        format_date = item.purchase_created_at.strftime("%Y-%m-%d")
                        if item.diff_hour <= 24:
                            if format_date in v24_data_dict.keys():
                                v24_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v24_data_dict[format_date]['count'] = v24_data_dict[format_date]['count'] + 1
                            else:
                                v24_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v24_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v24_total = v24_total + 1
                        elif item.diff_hour > 24 and item.diff_hour <= 30:
                            if format_date in v30_data_dict.keys():
                                v30_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v30_data_dict[format_date]['count'] = v30_data_dict[format_date]['count'] + 1
                            else:
                                v30_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v30_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v30_total = v30_total + 1
                        elif item.diff_hour > 30 and item.diff_hour <= 48:
                            if format_date in v48_data_dict.keys():
                                v48_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v48_data_dict[format_date]['count'] = v48_data_dict[format_date]['count'] + 1
                            else:
                                v48_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v48_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v48_total = v48_total + 1
                        else:
                            if format_date in v72_data_dict.keys():
                                v72_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v72_data_dict[format_date]['count'] = v72_data_dict[format_date]['count'] + 1
                            else:
                                v72_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v72_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v72_total = v72_total + 1
                        data_set.add(item.lab_number)
                purchase_sql = """SELECT date(t0.created_at) as created_at,COUNT(t0.id) AS cnt FROM oms_laborder_purchase_order_line AS t0 LEFT JOIN oms_laborder_purchase_order AS t1 ON t0.lpo_id=t1.id WHERE vendor='%s' GROUP BY date(t0.created_at)""" % vendor
                cursor.execute(purchase_sql)
                for item in namedtuplefetchall(cursor):
                    purchase_dict[str(item.created_at)] = item.cnt


        for key, val in v24_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
        for key, val in v30_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
        for key, val in v48_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
        for key, val in v72_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'

        return render(request, 'purchase_order_time_report.html',
                      {
                        "v24_data_dict": v24_data_dict,
                        "v30_data_dict": v30_data_dict,
                        "v48_data_dict": v48_data_dict,
                        "v72_data_dict": v72_data_dict,
                        "v24_total": v24_total,
                        "v30_total": v30_total,
                        "v48_total": v48_total,
                        "v72_total": v72_total,
                        "vendor": vendor,
                        "start_date": start_date,
                        "end_date": end_date
                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e)

def redirect_report_purchase_order_time_report_csv(request):
    v24_data_dict = collections.OrderedDict()
    v30_data_dict = collections.OrderedDict()
    v48_data_dict = collections.OrderedDict()
    v72_data_dict = collections.OrderedDict()
    purchase_dict = {}
    v24_total = 0
    v30_total = 0
    v48_total = 0
    v72_total = 0
    data_set = set()
    try:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        vendor = request.GET.get('vendor', '')
        if start_date != '' and end_date != '':
            if vendor == '9':
                sql = VD9_PURCHASE_DIFF_SQL % (end_date, start_date, end_date)
            else:
                sql = VD4_PURCHASE_DIFF_SQL % (end_date, start_date, end_date)

            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)

                for item in namedtuplefetchall(cursor):
                    if item.lab_number not in data_set:
                        format_date = item.purchase_created_at.strftime("%Y-%m-%d")
                        if item.diff_hour <= 24:
                            if format_date in v24_data_dict.keys():
                                v24_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v24_data_dict[format_date]['count'] = v24_data_dict[format_date]['count'] + 1
                            else:
                                v24_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v24_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v24_total = v24_total + 1
                        elif item.diff_hour > 24 and item.diff_hour <= 30:
                            if format_date in v30_data_dict.keys():
                                v30_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v30_data_dict[format_date]['count'] = v30_data_dict[format_date]['count'] + 1
                            else:
                                v30_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v30_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v30_total = v30_total + 1
                        elif item.diff_hour > 30 and item.diff_hour <= 48:
                            if format_date in v48_data_dict.keys():
                                v48_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v48_data_dict[format_date]['count'] = v48_data_dict[format_date]['count'] + 1
                            else:
                                v48_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v48_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v48_total = v48_total + 1
                        else:
                            if format_date in v72_data_dict.keys():
                                v72_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                                v72_data_dict[format_date]['count'] = v72_data_dict[format_date]['count'] + 1
                            else:
                                v72_data_dict[format_date] = {"itemlist": [], "count": 1, "ratio": 0}
                                v72_data_dict[format_date]['itemlist'].append({
                                    "lab_number": item.lab_number,
                                    "status_value": item.status_value,
                                    "reference_code": item.reference_code,
                                    "vender_created_at": item.vender_created_at,
                                    "purchase_created_at": item.purchase_created_at,
                                    "vendor": item.vendor,
                                    "diff_hour": item.diff_hour
                                })
                            v72_total = v72_total + 1
                        data_set.add(item.lab_number)
                purchase_sql = """SELECT date(t0.created_at) as created_at,COUNT(t0.id) AS cnt FROM oms_laborder_purchase_order_line AS t0 LEFT JOIN oms_laborder_purchase_order AS t1 ON t0.lpo_id=t1.id WHERE vendor='%s' GROUP BY date(t0.created_at)""" % vendor
                cursor.execute(purchase_sql)
                for item in namedtuplefetchall(cursor):
                    purchase_dict[str(item.created_at)] = item.cnt

        data_dict_csv=[]

        data_dict_csv.append({
            'date': '24H', 'ratio':'', 'lab_number': '','status_value':'',
            'reference_code':'','vender_created_at':'', 'purchase_created_at': '',
            'vendor':'', 'diff_hour':''
        })
        for key, val in v24_data_dict.items():
            val['ratio'] = str(round(float(val['count']) / float(purchase_dict[key]), 4) * 100) + '%'
            for item in val['itemlist']:
                data_dict_csv.append({
                                        'date': key, 'ratio': val['ratio'], 'lab_number': item['lab_number'],
                                        'status_value': item['status_value'], 'reference_code': item['reference_code'],
                                        'vender_created_at': item['vender_created_at'], 'purchase_created_at': item['purchase_created_at'],
                                        'vendor': item['vendor'], 'diff_hour': item['diff_hour']
                                    })
        data_dict_csv.append({
            'date': '30H', 'ratio':'', 'lab_number':'', 'status_value':'',
            'reference_code': '', 'vender_created_at':'', 'purchase_created_at':'',
            'vendor': '', 'diff_hour':''
        })
        for key, val in v30_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
            for item in val['itemlist']:
                data_dict_csv.append({
                                        'date': key, 'ratio': val['ratio'], 'lab_number': item['lab_number'],
                                        'status_value': item['status_value'], 'reference_code': item['reference_code'],
                                        'vender_created_at': item['vender_created_at'], 'purchase_created_at': item['purchase_created_at'],
                                        'vendor': item['vendor'], 'diff_hour': item['diff_hour']
                                    })

        data_dict_csv.append({
            'date':'48H', 'ratio':'', 'lab_number': '', 'status_value':'',
            'reference_code': '', 'vender_created_at':'', 'purchase_created_at':'',
            'vendor':'', 'diff_hour':''
        })
        for key, val in v48_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
            for item in val['itemlist']:
                data_dict_csv.append({
                                        'date': key, 'ratio': val['ratio'], 'lab_number': item['lab_number'],
                                        'status_value': item['status_value'], 'reference_code': item['reference_code'],
                                        'vender_created_at': item['vender_created_at'], 'purchase_created_at': item['purchase_created_at'],
                                        'vendor': item['vendor'], 'diff_hour': item['diff_hour']
                                    })

        data_dict_csv.append({
            'date': '72H', 'ratio':'', 'lab_number':'', 'status_value':'',
            'reference_code':'', 'vender_created_at': '', 'purchase_created_at':'',
            'vendor':'', 'diff_hour':''
        })
        for key, val in v72_data_dict.items():
            val['ratio'] = str(round(float(val['count'])/float(purchase_dict[key]),4) * 100) + '%'
            for item in val['itemlist']:
                data_dict_csv.append({
                                        'date': key, 'ratio': val['ratio'], 'lab_number': item['lab_number'],
                                        'status_value': item['status_value'], 'reference_code': item['reference_code'],
                                        'vender_created_at': item['vender_created_at'], 'purchase_created_at': item['purchase_created_at'],
                                        'vendor': item['vendor'], 'diff_hour': item['diff_hour']
                                    })

        import csv, codecs
        response = HttpResponse(content_type='text/csv')
        file_name = 'redirect_report_purchase_order_time_report'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '日期', '订单比率', '工厂订单号', '供应商状态', '供应商单号', '供应发货日期', '采购订单日期','供应商','时间差(小时)'
        ])
        for item in data_dict_csv:
            writer.writerow([
                item['date'],
                item['ratio'],
                item['lab_number'],
                item['status_value'],
                item['reference_code'],
                item['vender_created_at'],
                item['purchase_created_at'],
                item['vendor'],
                item['diff_hour']
            ])
        return response
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e)

def redirect_arrival_time_diff_report(request):
    try:
        data_list = []
        data_set = set()
        page = request.GET.get('page', 1)
        sql = ARRIVAL_TIME_DIFF_SQL
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                if item.lab_number not in data_set:
                    data_list.append({
                        "lab_number": item.lab_number,
                        "status_value": item.status_value,
                        "delivery_create_date": item.z_created_at,
                        "come_create_date": item.l_created_at,
                        "status": item.status,
                        "diff_hour": item.diff_hour
                    })
                    data_set.add(item.lab_number)

        paginator = Paginator(data_list, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)
        return render(request, 'arrival_time_diff_report.html',
                      {
                        "data_list": _items,
                        "paginator": paginator
                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e)

def redirect_arrival_time_diff_report_csv(request):
    _form_data = {}
    try:
        data_list = []
        data_set = set()
        sql = ARRIVAL_TIME_DIFF_SQL
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                if item.lab_number not in data_set:
                    data_list.append({
                        "lab_number": item.lab_number,
                        "status_value": item.status_value,
                        "delivery_create_date": item.z_created_at,
                        "come_create_date": item.l_created_at,
                        "status": item.status,
                        "diff_hour": item.diff_hour
                    })
                    data_set.add(item.lab_number)

        import csv, codecs

        response = HttpResponse(content_type='text/csv')
        file_name = 'arrival_time_diff_report'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            '工厂订单号', '供应商订单状态','供应商待发货时间', '来片登记时间', '工厂订单当前状态', '时间差（单位：小时）'
        ])

        for item in data_list:
            writer.writerow([
                item['lab_number'],
                item['status_value'],
                item['delivery_create_date'],
                item['come_create_date'],
                item['status'],
                item['diff_hour']
            ])

        return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


def laborder_doctor_report(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    _form_data = {}
    page = request.GET.get('page', 1)
    try:
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql = DOCTOR_LAB_SQL % (end_date, start_date, end_date)
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)

        _form_data['total'] = len(_items)

        # --页码-- 获取URL中除page外的其它参数
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

        return render(request, 'laborder_doctor_report.html', {
            'form_data': _form_data,
            'list': _items,
            'requestUrl': reverse('report_laborder_doctor_report'),
            'start_date': start_date,
            'end_date': end_date,
            'query_string': query_string,
            'paginator': paginator
        })
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)


@login_required
def laborder_doctor_report_csv(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    _form_data = {}
    page = request.GET.get('page', 1)
    try:
        _items = []
        if start_date !='' and end_date != '':
            with connections['pg_oms_query'].cursor() as cursor:
                sql = DOCTOR_LAB_SQL % (end_date, start_date, end_date)
                cursor.execute(sql)
                _items = namedtuplefetchall(cursor)
        import csv, codecs

        response = HttpResponse(content_type='text/csv')
        file_name = 'laborder_doctor_report'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)
        # 在下面添加要导出的属性即可
        writer.writerow([
            'Order Number', 'Lab Number','状态', '实际发货', '镜架', '数量', '订单镜片-SKU', '计划镜片', '实际镜片-SKU', '实际镜片', 'MGOrder日期', '生成PgOrder日期','下达日期', '审单时间差（小时）','终检合格日期','终检下达时间差（小时）','发货日期','发货下达时间差（小时）','妥投日期'
        ])

        for item in _items:
            writer.writerow([
                item.order_number, item.lab_number, item.status, item.act_ship_direction, item.frame, item.quantity, item.lens_sku, item.lens_name, item.act_lens_sku,
                item.act_lens_name, item.order_datetime, item.pg_create_at,item.create_at, item.pre_diff, item.qc_create_at, item.qc_diff, item.ship_create_at, item.ship_diff ,item.delivered_at
            ])

        return response
    except Exception as e:
        logging.debug(e)
        return HttpResponse(e)