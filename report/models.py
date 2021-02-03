# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q

from django.utils import timezone
# Create your models here.
from django.urls import reverse
import logging
from time import strftime
from django.db import connections
from django.db import transaction
from decimal import Decimal

from oms.models import OperationLog, PgOrderItem
from oms.models.ordertracking_models import OrderTracking
from shipment.models import pre_delivery_line
from util.db_helper import *

from oms.models.order_models import LabOrder, PgOrder
from util.time_delta import *
from util.base_type import base_type
from util.response import response_message
from const import *
from django.core import serializers
from util.dict_helper import dict_helper
import simplejson as json
from util.format_helper import *


class statistical_analysis:
    key = ''
    title = ''
    number = ''
    url = '#'
    index = 0
    # style = 'bg-red-gradient'
    style = 'bg-primary'


class status_choice:
    key = ''
    value = ''


class statistical_analysis_laborder:
    _time_dimentions = []

    _status_dimentions = []

    '''
    STATUS_CHOICES = (
        ('', '新订单'),
        ('REQUEST_NOTES', '出库申请'),
        ('FRAME_OUTBOUND', '镜架出库'),
        ('PRINT_DATE', '打印'),
        # ('TINT', '染色'),
        # ('RX_LAB', '车房'),
        # ('ADD_HARDENED', '加硬'),
        # ('COATING', '加膜'),

        ('INITIAL_INSPECTION', '初检'),
        ('LENS_RECEIVE', '镜片收货'),

        ('ASSEMBLING', '装配'),

        # ('SHAPING', '整形'),
        ('FINAL_INSPECTION', '终检'),
        # ('PURGING', '清洗'),

        ('ORDER_MATCH', '订单配对'),
        ('PICKING', '已拣配'),
        # ('PACKAGE', '包装'),
        ('SHIPPING', '发货'),
        ('COMPLETE', '完成'),
        ('ONHOLD', '暂停'),
        ('CANCELLED', '取消'),
        ('REDO', '重做'),
    )
    '''
    STATUS_CHOICES = LabOrder.STATUS_CHOICES

    def time_dimentions_new(self):
        td = statistical_analysis()
        with connections['pg_oms_query'].cursor() as cursor:
            new_sql = """SELECT COUNT(*) AS cnt FROM oms_laborder 
                         WHERE is_enabled = TRUE 
                               AND status ='' OR `status` is NULL
                               AND create_at>= '%s'""" % time_delta()
            cursor.execute(new_sql)
            results = namedtuplefetchall(cursor)
        td.index = 0
        td.title = '新订单'
        td.number = results[0].cnt
        td.url = reverse('laborder_list_v2') + "?filter=new&status=all&vendor=all"
        return td

    def time_dimentions_week(self):
        td = statistical_analysis()
        with connections['pg_oms_query'].cursor() as cursor:
            week_sql = """SELECT COUNT(*) AS cnt FROM oms_laborder 
                          WHERE is_enabled = TRUE 
                               AND create_at>= '%s'""" % time_delta_week()
            cursor.execute(week_sql)
            results = namedtuplefetchall(cursor)
        td.index = 0
        td.title = '最近一周'
        td.number = results[0].cnt
        td.url = reverse('laborder_list_v2')
        return td

    def time_dimentions_month(self):
        td = statistical_analysis()
        with connections['pg_oms_query'].cursor() as cursor:
            month_sql = """SELECT COUNT(*) AS cnt FROM oms_laborder 
                           WHERE is_enabled = TRUE 
                               AND create_at>= '%s'""" % time_delta_month()
            cursor.execute(month_sql)
            results = namedtuplefetchall(cursor)
        td.index = 0
        td.title = '最近一月'
        td.number = results[0].cnt
        td.url = reverse('laborder_list_v2') + "?filter=month&status=all&vendor=all"
        return td

    def time_dimentions_all(self):
        td = statistical_analysis()
        with connections['pg_oms_query'].cursor() as cursor:
            all_sql = """SELECT COUNT(*) AS cnt FROM oms_laborder 
                           WHERE is_enabled = TRUE 
                               AND create_at>= '%s'""" % time_delta()

            cursor.execute(all_sql)
            results = namedtuplefetchall(cursor)

        td.index = 0
        td.title = '当前阶段总订单数'
        td.number = results[0].cnt
        td.url = reverse('laborder_list_v2') + "?filter=all&status=all&vendor=all"
        return td

    def status_dimentions(self):
        self._status_dimentions = []
        status_dict = {'NEW': {'key': 'NEW', 'number': 0, 'title': '新订单',
                               'url': reverse('laborder_list_v2') + "?filter=new&status=all&vendor=all",
                               'style': 'bg-primary'},
                       'REQUEST_NOTES': {'key': 'REQUEST_NOTES', 'number': 0, 'title': '出库申请', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=REQUEST_NOTES&vendor=all", 'style': 'bg-primary'},
                       'FRAME_OUTBOUND': {'key': 'FRAME_OUTBOUND', 'number': 0, 'title': '镜架出库', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=FRAME_OUTBOUND&vendor=all", 'style': 'bg-primary'},

                       'LENS_OUTBOUND': {'key': 'LENS_OUTBOUND', 'number': 0, 'title': '镜片出库',
                                         'url': reverse(
                                             'laborder_list_v2') + "?filter=all&status=LENS_OUTBOUND&vendor=all",
                                         'style': 'bg-primary'},

                       'PRINT_DATE': {'key': 'PRINT_DATE', 'number': 0, 'title': '单证打印',
                                      'url': reverse('laborder_list_v2') + "?filter=all&status=PRINT_DATE&vendor=all",
                                      'style': 'bg-primary'},

                       'LENS_REGISTRATION': {'key': 'LENS_REGISTRATION', 'number': 0, 'title': '来片登记', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=LENS_REGISTRATION&vendor=all",
                                             'style': 'bg-primary'},
                       'LENS_RETURN': {'key': 'LENS_RETURN', 'number': 0, 'title': '镜片退货',
                                       'url': reverse('laborder_list_v2') + "?filter=all&status=LENS_RETURN&vendor=all",
                                       'style': 'bg-primary'},
                       'LENS_RECEIVE': {'key': 'LENS_RECEIVE', 'number': 0, 'title': '镜片收货', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=LENS_RECEIVE&vendor=all", 'style': 'bg-primary'},
                       'ASSEMBLING': {'key': 'ASSEMBLING', 'number': 0, 'title': '待装配',
                                      'url': reverse('laborder_list_v2') + "?filter=all&status=ASSEMBLING&vendor=all",
                                      'style': 'bg-primary'},
                       'ASSEMBLED': {'key': 'ASSEMBLED', 'number': 0, 'title': '装配完成',
                                     'url': reverse('laborder_list_v2') + "?filter=all&status=ASSEMBLED&vendor=all",
                                     'style': 'bg-primary'},
                       'GLASSES_RECEIVE': {'key': 'GLASSES_RECEIVE', 'number': 0, 'title': '成镜收货', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=GLASSES_RECEIVE&vendor=all",
                                           'style': 'bg-primary'},
                       'FINAL_INSPECTION': {'key': 'FINAL_INSPECTION', 'number': 0, 'title': '终检', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=FINAL_INSPECTION&vendor=all",
                                            'style': 'bg-primary'},
                       'FINAL_INSPECTION_YES': {'key': 'FINAL_INSPECTION_YES', 'number': 0, 'title': '终检合格',
                                                'url': reverse(
                                                    'laborder_list_v2') + "?filter=all&status=FINAL_INSPECTION_YES&vendor=all",
                                                'style': 'bg-primary'},
                       'FINAL_INSPECTION_NO': {'key': 'FINAL_INSPECTION_NO', 'number': 0, 'title': '终检不合格',
                                               'url': reverse(
                                                   'laborder_list_v2') + "?filter=all&status=FINAL_INSPECTION_NO&vendor=all",
                                               'style': 'bg-primary'},
                       'GLASSES_RETURN': {'key': 'GLASSES_RETURN', 'number': 0, 'title': '成镜返工', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=GLASSES_RETURN&vendor=all", 'style': 'bg-primary'},
                       'COLLECTION': {'key': 'COLLECTION', 'number': 0, 'title': '归集',
                                      'url': reverse('laborder_list_v2') + "?filter=all&status=COLLECTION&vendor=all",
                                      'style': 'bg-primary'},
                       'PRE_DELIVERY': {'key': 'PRE_DELIVERY', 'number': 0, 'title': '预发货', 'url': reverse(
                           'laborder_list_v2') + "?filter=all&status=PRE_DELIVERY&vendor=all", 'style': 'bg-primary'},
                       'PICKING': {'key': 'PICKING', 'number': 0, 'title': '已拣配',
                                   'url': reverse('laborder_list_v2') + "?filter=all&status=PICKING&vendor=all",
                                   'style': 'bg-primary'},
                       'ORDER_MATCH': {'key': 'ORDER_MATCH', 'number': 0, 'title': '订单配对',
                                       'url': reverse('laborder_list_v2') + "?filter=all&status=ORDER_MATCH&vendor=all",
                                       'style': 'bg-primary'},
                       'BOXING': {'key': 'BOXING', 'number': 0, 'title': '装箱',
                                  'url': reverse('laborder_list_v2') + "?filter=all&status=BOXING&vendor=all",
                                  'style': 'bg-primary'},
                       'ONHOLD': {'key': 'ONHOLD', 'number': 0, 'title': '暂停',
                                  'url': reverse('laborder_list_v2') + "?filter=all&status=ONHOLD&vendor=all",
                                  'style': 'bg-primary'},
                       'CANCELLED': {'key': 'CANCELLED', 'number': 0, 'title': '取消',
                                     'url': reverse('laborder_list_v2') + "?filter=all&status=CANCELLED&vendor=all",
                                     'style': 'bg-primary'},
                       'R2HOLD': {'key': 'R2HOLD', 'number': 0, 'title': '申请暂停',
                                  'url': reverse('laborder_list_v2') + "?filter=all&status=R2HOLD&vendor=all",
                                  'style': 'bg-primary'},
                       'R2CANCEL': {'key': 'R2CANCEL', 'number': 0, 'title': '申请取消',
                                    'url': reverse('laborder_list_v2') + "?filter=all&status=R2CANCEL&vendor=all",
                                    'style': 'bg-primary'},
                       'REDO': {'key': 'REDO', 'number': 0, 'title': '重做',
                                'url': reverse('laborder_list_v2') + "?filter=all&status=REDO&vendor=all",
                                'style': 'bg-primary'},
                       }

        with connections['pg_oms_query'].cursor() as cursor:
            sql = """SELECT COUNT(*) AS cnt,`status` FROM oms_laborder 
                     WHERE is_enabled = TRUE 
						AND create_at >= '%s'
                        AND status <>'' AND `status` is not NULL AND `status` not in ('COMPLETE', 'SHIPPING','INITIAL_INSPECTION', 'TINT', 'RX_LAB', 'ADD_HARDENED', 'COATING', 'SHAPING', 'PURGING', 'PACKAGE', 'COMPLETE')
                     GROUP BY `status` 
                     union ALL SELECT COUNT(*) AS cnt,`status` FROM oms_laborder 
                     WHERE is_enabled = TRUE 
                        AND status ='' OR `status` is NULL 
						AND create_at >= '%s' 
                        """ % (time_delta(), time_delta())
            cursor.execute(sql)

            for item in namedtuplefetchall(cursor):
                for key, value in status_dict.items():
                    if item.status:
                        item_key = item.status
                    else:
                        item_key = 'NEW'

                    if item_key == key:
                        value['number'] = item.cnt

        index = 0
        for sta in self.STATUS_CHOICES:
            if sta[0] == '':
                key = 'NEW'
            else:
                key = sta[0]

            if key in status_dict.keys():
                td = statistical_analysis()
                td.index = index
                td.key = status_dict[key]['key']
                td.title = status_dict[key]['title']
                td.number = status_dict[key]['number']
                td.url = status_dict[key]['url']
                td.style = status_dict[key]['style']
                self._status_dimentions.append(td)

        return self._status_dimentions


class exceed_laborders:
    _exceed_dimentions = []

    STATUS_CHOICES = (
        ('', '新订单'),
        ('REQUEST_NOTES', '出库申请'),
        ('FRAME_OUTBOUND', '镜架出库'),
        ('PRINT_DATE', '镜片生产'),
        ('INITIAL_INSPECTION', '镜片初检'),
        ('LENS_RECEIVE', '镜片收货'),
        ('ASSEMBLING', '待装配'),
        ('FINAL_INSPECTION', '终检合格'),
        ('PICKING', '预发货'),
        ('ORDER_MATCH', '订单配对'),
        ('ONHOLD', '暂停'),
        ('REDO', '重做'),
    )

    _vendor_dimentions = []

    VENDOR_CHOICES = (
        # ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    )

    def exceed_dimentions(self, results):
        self._exceed_dimentions = []

        exceed_choices_list = []

        for sta in LabOrder.STATUS_CHOICES:
            sc = status_choice()
            sc.key = sta[0]
            sc.value = sta[1]
            if not sc.key == 'SHIPPING' and not sc.key == 'CANCELLED' and not sc.key == 'DELIVERED':
                exceed_choices_list.append(sc)

        index = 0

        for sta in exceed_choices_list:
            td = statistical_analysis()

            td.url = reverse('laborder_list_v2') + "?filter=all&status=" + sta.key + "&vendor=all&sorted=set_time"

            querys = results.filter(status=sta.key)

            nums = querys.count()
            # nums_vd1 = querys.filter(vendor=1).count()
            # nums = '%d (%d)' % (nums, nums_vd1)
            td.index = index
            td.key = sta.key
            td.title = sta.value
            td.number = nums

            if td.key == '':
                td.style = 'bg-primary'

            if td.key == 'PRINT_DATE':
                td.style = 'bg-primary'

            # if td.key == 'LENS_RECEIVE':
            #    td.style = 'bg-primary-gradient'

            if td.key == 'ORDER_MATCH':
                td.style = 'bg-primary'

            if td.key == 'SHIPPING':
                td.style = 'bg-primary'

            if td.key == 'CANCELLED':
                td.style = 'bg-primary'

            index += 1

            self._exceed_dimentions.append(td)

        return self._exceed_dimentions

    def vendor_dimentions(self, results):
        td = statistical_analysis()

        self._vendor_dimentions = []

        vendor_choices_list = []

        for sta in self.VENDOR_CHOICES:
            sc = status_choice()
            sc.key = sta[0]
            sc.value = sta[1]
            vendor_choices_list.append(sc)

        index = 0

        for sta in vendor_choices_list:
            td = statistical_analysis()

            td.url = reverse('laborder_list_v2') + "?filter=all&status=all&vendor=" + sta.key + "&sorted=set_time"

            # querys = results.filter(vendor=sta.key).filter(Q(status='')
            #                                                | Q(status='REQUEST_NOTES')
            #                                                | Q(status='FRAME_OUTBOUND')
            #                                                | Q(status='PRINT_DATE')
            #                                                | Q(status='INITIAL_INSPECTION')
            #                                                | Q(status='LENS_RECEIVE')
            #                                                | Q(status='ASSEMBLING')
            #                                                | Q(status='FINAL_INSPECTION')
            #                                                | Q(status='PICKING')
            #                                                | Q(status='ORDER_MATCH')
            #                                                | Q(status='ONHOLD')
            #                                                | Q(status='REDO')
            #                                                )

            querys = results.filter(vendor=sta.key).filter(
                ~Q(status='SHIPPING'),
                ~Q(status='CANCELLED')
            )

            nums = querys.count()
            # nums_vd1 = querys.filter(vendor=1).count()
            # nums = '%d (%d)' % (nums, nums_vd1)
            td.index = index
            td.key = sta.key
            td.title = sta.value
            td.number = nums

            index += 1

            self._vendor_dimentions.append(td)

        return self._vendor_dimentions


class lens_registration_analysis:
    good = 0
    general = 0
    bad = 0
    unship = 0

    report_day = ''


class serie:
    name = ''
    type = 'line'
    stack = ''
    data = []


class report_line_stack_struct:
    vendor = ''
    title = ''
    legend = []
    xaxis = []
    series = []
    good = []
    general = []
    bad = []
    unship = []


class lens_report(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='LREO', editable=False)

    REPORT_TYPE_CHOICES = (
        ('LR', 'Lens Registration Report'),
    )

    report_type = models.CharField(u'Report Type', max_length=128, default='LR', blank=True, null=True,
                                   choices=REPORT_TYPE_CHOICES)
    report_day = models.CharField(u'Report Day', max_length=128, default='', null=True, blank=True)

    @property
    def get_lines(self):
        return lens_report_line.objects.filter(lr=self)

    def clear_lines(self):
        lens_report_line.objects.filter(lr=self).delete()


class lens_report_line(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='LREL', editable=False)

    PERIOD_CHOICES = (
        ('7', 'Last 7 Days'),
        ('30', 'Current Month'),
    )

    lr = models.ForeignKey(lens_report, models.CASCADE,
                           blank=True,
                           null=True, editable=False)

    period = models.CharField(u'Period', max_length=128, default='', null=True, blank=True,
                              choices=PERIOD_CHOICES)
    range = models.CharField(u'Range', max_length=128, default='', null=True, blank=True)

    good = models.IntegerField(u'Quantity', default=0)
    general = models.IntegerField(u'Quantity', default=0)
    bad = models.IntegerField(u'Quantity', default=0)
    unship = models.IntegerField(u'Quantity', default=0)
    report_day = models.CharField(u'Report Day', max_length=128, default='', null=True, blank=True)

    total = models.IntegerField(u'Quantity', default=0)


class lens_report_control:
    def generate(self):
        rm = self.generate_7()
        return rm

    def generate_7(self):
        rm = response_message()
        try:

            with transaction.atomic():

                vendors = ['1', '2', '3', '4', '5']

                vendors = ['2', '3', '4', '5', '6', '7']

                td = datetime.datetime.now()

                tday_string = td.strftime('%Y-%m-%d')

                lrs = lens_report.objects.filter(report_day=tday_string)
                if lrs.count() > 0:
                    lr = lrs[0]
                else:
                    lr = lens_report()

                lr.report_day = tday_string
                lr.report_type = 'LR'

                lr.save()

                lr.clear_lines()

                for vd in vendors:

                    days = []
                    lras = []

                    now_time = datetime.datetime.now()
                    # now_time = now_time + datetime.timedelta(days=-30)

                    for i in range(7):
                        n = 7 - i
                        yes_time = now_time + datetime.timedelta(days=-1 * n)
                        yes_time_nyr = yes_time.strftime('%Y-%m-%d')
                        days.append(yes_time_nyr)

                    days2 = []

                    for i in range(7):
                        n = 7 - i
                        yes_time = now_time + datetime.timedelta(days=-1 * n)
                        yes_time_nyr = yes_time
                        days2.append(yes_time_nyr)

                    series = []

                    for cur_day in days2:

                        # cur_day = datetime.datetime.now() + datetime.timedelta(days=-22)
                        yes_day = cur_day + datetime.timedelta(days=-1)

                        str_yes_day = yes_day.strftime('%Y-%m-%d')
                        str_cur_day = cur_day.strftime('%Y-%m-%d')

                        year = cur_day.year
                        month = cur_day.month
                        day = cur_day.day

                        logging.debug('----------------------------------------')

                        lra = lens_registration_analysis()

                        sql = 'select * from oms_laborder where (`oms_laborder`.`create_at` <= "%s" ' \
                              'AND `oms_laborder`.`create_at` > "%s" and vendor=%s)' % (
                                  str_cur_day, str_yes_day, vd)

                        lbos = LabOrder.objects.raw(sql)

                        logging.debug(lbos.query)

                        lra.total = len(list(lbos))
                        lra.report_day = str_cur_day

                        for lbo in lbos:

                            if lbo.status == None or lbo.status == '' or lbo.days_of_lens_registration < 0:
                                lra.unship += 1
                            else:
                                if lbo.lens_type == 'C':
                                    if lbo.days_of_lens_registration >= 0 and lbo.days_of_lens_registration <= 2:
                                        lra.good += 1
                                    elif lbo.days_of_lens_registration > 2 and lbo.days_of_lens_registration <= 4:
                                        lra.general += 1
                                    else:
                                        lra.bad += 1
                                else:
                                    if lbo.days_of_lens_registration >= 0 and lbo.days_of_lens_registration <= 1:
                                        lra.good += 1
                                    elif lbo.days_of_lens_registration > 1 and lbo.days_of_lens_registration <= 3:
                                        lra.general += 1
                                    else:
                                        lra.bad += 1

                        logging.debug(lra.__dict__)
                        lras.append(lra)

                    for lra in lras:
                        lrl = lens_report_line()
                        lrl.lr = lr
                        lrl.period = '7'
                        lrl.good = lra.good
                        lrl.general = lra.general
                        lrl.bad = lra.bad
                        lrl.unship = lra.unship

                        lrl.total = lra.good + lra.general + lra.bad + lra.unship

                        lrl.range = vd

                        lrl.report_day = lra.report_day
                        lrl.save()

                return rm
        except Exception as e:
            rm.capture_execption(e)

        return rm

    def generate_report_front(self):

        rm = response_message()

        rlsss = []

        vendors = ['1', '2', '3', '4', '5']
        vendors = ['2', '3', '4', '5', '6', '7']

        td = datetime.datetime.now()
        tday_string = td.strftime('%Y-%m-%d')

        lrs = lens_report.objects.filter(report_day=tday_string)

        lr = None
        if lrs.count() > 0:
            lr = lrs[0]
        else:
            rm.code = -2
            rm.message = 'No Data'
            return rm

        good = None
        general = None
        bad = None
        unship = None

        for vd in vendors:
            rlss = None
            rlss = report_line_stack_struct()
            rlss.vendor = vd
            rlss.title = 'Vendor %s' % vd
            rlss.legend = ['good', 'general', 'bad', 'unship']

            rlss.xaxis = []

            lrls = lens_report_line.objects.filter(lr=lr, range=vd)
            good = []
            general = []
            bad = []
            unship = []
            for lrl in lrls:
                rlss.xaxis.append(lrl.report_day)
                if lrl.total > 0:
                    g1 = float(lrl.good) / float(lrl.total) * 100
                    g2 = float(lrl.general) / float(lrl.total) * 100
                    g3 = float(lrl.bad) / float(lrl.total) * 100
                    g4 = float(lrl.unship) / float(lrl.total) * 100

                    good.append(Decimal(g1).quantize(Decimal('0.00')))
                    general.append(Decimal(g2).quantize(Decimal('0.00')))
                    bad.append(Decimal(g3).quantize(Decimal('0.00')))
                    unship.append(Decimal(g4).quantize(Decimal('0.00')))
                else:
                    good.append(0)
                    general.append(0)
                    bad.append(0)
                    unship.append(0)

            rlss.good = good
            rlss.general = general
            rlss.bad = bad
            rlss.unship = unship

            rlsss.append(rlss)

        rm.obj = rlsss

        return rm

        # series = []
        #
        # lras = []
        #
        # serie = {}
        # serie['Name'] = 'Good'
        # serie['Type'] = 'Line'
        # serie['itemStyle'] = {
        #     "normal": {
        #         "lineStyle": {
        #             "color": '#02C874'
        #         }
        #     }
        # }

        # data = []
        # for lra in lras:
        #     data.append(float(lra.good) / float(lra.total) * 100)
        # serie['Data'] = data
        # series.append(serie)
        #
        # logging.debug(serie)
        #
        # serie = {}
        # serie['Name'] = 'General'
        # serie['Type'] = 'Line'
        # serie['itemStyle'] = {
        #     "normal": {
        #         "lineStyle": {
        #             "color": '#FF8000'
        #         }
        #     }
        # }
        # data = []
        # for lra in lras:
        #     data.append(float(lra.general) / float(lra.total) * 100)
        # serie['Data'] = data
        # series.append(serie)
        #
        # logging.debug(serie)
        #
        # serie = {}
        # serie['Name'] = 'Bad'
        # serie['Type'] = 'Line'
        # serie['itemStyle'] = {
        #     "normal": {
        #         "lineStyle": {
        #             "color": '#CE0000'
        #         }
        #     }
        # }
        # data = []
        # for lra in lras:
        #     data.append(float(lra.bad) / float(lra.total) * 100)
        # serie['Data'] = data
        # series.append(serie)
        #
        # logging.debug(serie)
        #
        # serie = {}
        # serie['Name'] = 'Unship'
        # serie['Type'] = 'Line'
        # serie['itemStyle'] = {
        #     "normal": {
        #         "lineStyle": {
        #             "color": '#5CADAD'
        #         }
        #     }
        # }
        # data = []
        # for lra in lras:
        #     data.append(float(lra.unship) / float(lra.total) * 100)
        # serie['Data'] = data
        # series.append(serie)
        #
        # logging.debug(serie)


class order_report_control:
    def generate_v2(self, filter):
        rm = response_message()
        try:
            filter = filter

            # logging.debug('--------------------generate_v2--------------------');
            # logging.debug('filter: %s' % filter)

            items = []
            td = timezone.now().date()
            if filter == '':
                return rm

            filter = int(filter)
            yd = td + datetime.timedelta(days=-1 * filter)
            day = "date(\'%s.%s.%s\')" % (yd.year, yd.month, yd.day)

            # logging.debug(day)

            with connections['default'].cursor() as cursor:
                logging.debug(day)
                sql = SQL_ORDER_REPORT % (day, day, day, day, day, day, day, day)
                logging.debug(sql)
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
                # logging.debug(results)

                for r in range(len(results)):
                    item = {}
                    item['report_day'] = results[r].report_day
                    item['web_order'] = results[r].web_order
                    item['undisposed'] = results[r].undisposed
                    item['web_glasses_qty'] = results[r].web_glasses_qty
                    item['lad_order'] = results[r].lad_order
                    item['lens_receive'] = results[r].lens_receive
                    item['glasses_recive'] = results[r].glasses_recive
                    item['picking'] = results[r].picking

                    web_glasses_qty = item['web_glasses_qty']
                    # logging.debug(web_glasses_qty)

                    picking = item['picking']
                    # logging.debug(picking)
                    rate = '-'

                    if web_glasses_qty:
                        # logging.debug(float(web_glasses_qty))
                        fl_web_glasses_qty = float(web_glasses_qty)
                        fl_picking = float(picking)
                        if fl_web_glasses_qty > 0:
                            rate = fl_picking / fl_web_glasses_qty
                            rate = '%.2f%%' % (rate * 100)
                        else:
                            rate = '-'

                    item['picking_pct'] = rate
                    items.append(item)

            rm.obj = items
            return rm

        except Exception as e:
            rm.capture_execption(e)
            logging.debug(rm.exception)

        return rm


class customize_report(base_type):
    index = models.IntegerField(u'Index', default=1000)
    group = models.CharField(u'Group', max_length=128, default='', null=True, blank=True, )  # 同时用来区分权限
    code = models.CharField(u'Code', max_length=128, default='', unique=True)  # 增加唯一性限制
    name = models.CharField(u'Name', max_length=512, default='', null=True, blank=True, )
    parameters_sample = models.TextField(u'Parameters Sample', default='', blank=True, null=True)
    is_need_parameters = models.BooleanField(u'Is Need Parameters', default=False)
    sql_script = models.TextField(u'SQL SCRIPT', default='', blank=True, null=True)
    comments = models.TextField(u'Comments', default='', blank=True, null=True)


class customize_report_query_history(base_type):
    code = models.CharField(u'Code', max_length=128, default='')  # 增加唯一性限制
    name = models.CharField(u'Name', max_length=512, default='', null=True, blank=True, )
    event_type = models.CharField(u'Event Type', max_length=128, default='', null=True, blank=True)  # 增加唯一性限制
    sql_script = models.TextField(u'SQL SCRIPT', default='', blank=True, null=True)
    results_count = models.IntegerField(u'Result Count', default=0)


class customize_report_controller:
    customize_reports = []

    def __init__(self):
        '''
        以下是样例代码，暂时保留
        '''

        crs = []

        cr = customize_report()
        cr.index = 0
        cr.group = 'SALES'
        cr.code = 'LAB_WEB_DIFF_5'
        cr.name = '查询所有工厂库存量大于网站所有分类的产品数量之和，并且差额大于5的SKU清单'
        cr.parameters_sample = '该查询无需参数'
        cr.sql_script = '''
                /*
                    查询所有工厂库存量>网站所有分类的产品数量之和，并且差额>5的SKU清单
                */

                SELECT sku, name, quantity
                , quantity - (web_women_quantity + web_men_quantity + web_kids_quantity) AS diff
                , web_women_quantity, web_men_quantity, web_kids_quantity, status
                FROM wms_inventory_struct
                WHERE quantity - (web_women_quantity + web_men_quantity + web_kids_quantity) > 5
                ORDER BY status
                LIMIT 10000
                '''
        crs.append(cr)

        cr = customize_report()
        cr.index = 1
        cr.group = 'PRODUCTION'
        cr.code = 'LAB_PRODUCTION_SPEED'
        cr.name = '生产速度报表'

        cr.sql_script = '''
            /* 
                各VD出货速度分析报表 
                # 增加车房片区分
            */
            SELECT t0.id, t0.lab_number, lens.is_rx_lab, t0.vendor, t0.workshop, t0.create_at AS in_lab_date
                , t1.created_at AS puchase_date, TIMESTAMPDIFF(HOUR, t0.create_at, t1.created_at) AS purchase_time
                , MAX(t5.created_at) AS ship_date
                , TIMESTAMPDIFF(HOUR, t1.created_at, MAX(t5.created_at)) AS ship_time
                , CASE 
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 48 THEN 48
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 48
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 72 THEN 72
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 72
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 96 THEN 96
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 96
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 120 THEN 120
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 120
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 144 THEN 144
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 144
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 168 THEN 168
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 168
                    AND TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) <= 192 THEN 192
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) > 192 THEN 200
                    WHEN TIMESTAMPDIFF(HOUR, t1.created_at, t5.created_at) IS NULL THEN 400
                        END AS production_target
                    FROM oms_laborder t0
                        LEFT JOIN oms_labproduct lens ON t0.act_lens_sku = lens.sku
                        LEFT JOIN oms_laborder_request_notes_line t1 ON t0.id = t1.laborder_entity_id
                        LEFT JOIN shipment_pre_delivery_line t5 ON t0.id = t5.lab_order_entity_id
                    WHERE t0.status <> 'CANCELLED'
                        AND t0.create_at >= DATE('2018.09.01')
                            # 增加车房片区分
                            # 
                        AND (t0.vendor <> 0
                        AND t0.vendor <> 1000)
                        AND t0.create_at >= DATE('%s')
                        AND t0.create_at <= DATE('%s')
                        AND lens.is_rx_lab = %s
                    GROUP BY t0.vendor, t0.id
                    LIMIT 10000
                    '''

        cr.parameters_sample = '参数示例: "2018.12.01"|"2018.12.31"|1'
        cr.is_need_parameters = True
        crs.append(cr)

        cr = customize_report()

        cr.index = 2
        cr.group = 'PRODUCTION'
        cr.code = 'LAB_VENDOR_SPEED'
        cr.name = '供应商供货速度报表'
        cr.parameters_sample = '该查询无需参数'
        crs.append(cr)

        self.customize_reports = crs

        logging.debug(self.customize_reports)

    def get_all(self):
        query_sets = customize_report.objects.filter(is_enabled=True).order_by('group', 'index', 'id')
        logging.debug(query_sets.query)
        return query_sets

    def get_by_code(self, code=0):
        try:
            cr = customize_report.objects.get(code=code)
            return cr
        except Exception as e:
            logging.debug(str(e))
            return None

    def log_query(self, request, parameters):
        try:
            if request:
                user_id = request.user.id
                user_name = request.user.username
            else:
                user_id = 0
                user_name = 'System'

            crqh = customize_report_query_history()
            crqh.user_id = user_id
            crqh.user_name = user_name
            crqh.event_type = parameters.get('event_type', '')
            crqh.code = parameters.get('code', '')
            crqh.name = parameters.get('name', '')
            crqh.sql_script = parameters.get('sql_script', '')

            crqh.save()

        except Exception as ex:
            logging.error(str(ex))


class dashboard_controller:
    def get_not_inlad(self):
        rm = response_message()
        try:
            sql_total = """
            select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                and is_enabled=True
                and is_inlab=False;
            """

            sql_processing = """
            select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                and is_enabled=True
                and status='processing'
                and is_inlab=False;
            """

            sql_holded = """
            select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                and is_enabled=True
                and status='holded'
                and is_inlab=False;
            """

            sql_canceled = """
                    select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                        and is_enabled=True
                        and status='canceled'
                        and is_inlab=False;
                    """

            sql_shipped = """
                    select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                        and is_enabled=True
                        and status='shipped'
                        and is_inlab=False;
                    """
            sql_closed = """
                    select count(id) as qty from oms_pgorder where create_at>'2019.01.01'
                        and is_enabled=True
                        and status='closed'
                        and is_inlab=False;
                    """

            items = {}

            logging.debug('get not inlab')

            results = self.__get_results(sql_total)
            items["total"] = results[0].qty
            results = self.__get_results(sql_processing)
            items["processing"] = results[0].qty
            results = self.__get_results(sql_holded)
            items["holded"] = results[0].qty
            results = self.__get_results(sql_canceled)
            items["canceled"] = results[0].qty
            results = self.__get_results(sql_shipped)
            items["shipped"] = results[0].qty
            results = self.__get_results(sql_closed)
            items["closed"] = results[0].qty

            logging.debug(items)

            rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def get_new_laborders(self):
        rm = response_message()
        now_date = datetime.datetime.utcnow()
        timedel = now_date + datetime.timedelta(days=-90)
        try:
            sql_total = """
            select count(id) as qty from oms_laborder where (status='' or status is null)
            and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            sql_vd_0 = """
            select count(id) as qty from oms_laborder where (status='' or status is null) and 
            (vendor='0')
            and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            sql_vd_1000 = """
              select count(id) as qty from oms_laborder where (status='' or status is null) and 
              (vendor='1000')
              and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            sql_vd_2_4_7_8 = """
            select count(id) as qty from oms_laborder where (status='' or status is null) and 
            (vendor='2' or vendor='4' or vendor ='7' or vendor ='8')
            and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            sql_vd_5_6_9_10 = """
            select count(id) as qty from oms_laborder where (status='' or status is null) and 
            (vendor='5' or vendor='6' or vendor='9' or vendor='10')
            and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            items = {}

            results = self.__get_results(sql_total)
            items["total"] = results[0].qty
            results = self.__get_results(sql_vd_0)
            items["vd_0"] = results[0].qty
            results = self.__get_results(sql_vd_1000)
            items["vd_1000"] = results[0].qty
            results = self.__get_results(sql_vd_2_4_7_8)
            items["vd_2_4_7_8"] = results[0].qty
            results = self.__get_results(sql_vd_5_6_9_10)
            items["vd_5_6_9_10"] = results[0].qty

            logging.debug(items)

            rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def get_processing_laborders(self):
        rm = response_message()
        now_date = datetime.datetime.utcnow()
        timedel = now_date + datetime.timedelta(days=-90)
        try:

            base_paras = """
            status in(
                'PRINT_DATE'
                ,'LENS_REGISTRATION'
                ,'LENS_RETURN'
                ,'LENS_RECEIVE'
                ,'ASSEMBLING'
                )
                and date(convert_tz(create_at,@@session.time_zone,'+8:00'))>date('%s')
            """ % timedel

            sql_total = """
            select count(id) as qty from oms_laborder where (%s)
            """ % base_paras

            logging.debug(sql_total)

            sql_vd_2_4_7_8 = """
            select count(id) as qty from oms_laborder where (%s) and 
            (vendor='2' or vendor='4' or vendor ='7' or vendor ='8')
            """ % base_paras

            vd_5_6_9_10 = """
            select count(id) as qty from oms_laborder where (%s) and 
            (vendor='5' or vendor='6' or vendor='9' or vendor='10' )
            """ % base_paras

            items = {}

            logging.debug("-----------")

            results = self.__get_results(sql_total)
            items["total"] = results[0].qty
            results = self.__get_results(sql_vd_2_4_7_8)
            items["vd_2_4_7_8"] = results[0].qty
            results = self.__get_results(vd_5_6_9_10)
            items["vd_5_6_9_10"] = results[0].qty

            logging.debug(items)

            rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def get_today_complete_laborders(self):
        rm = response_message()
        try:
            nowtime = timezone.now().strftime('%Y-%m-%d')
            # nowtime = '2019.01.01'
            base_paras = """
            status in(
                'ASSEMBLED'
                ,'GLASSES_RECEIVE'
                ,'FINAL_INSPECTION'
                ,'FINAL_INSPECTION_YES'
                ,'PRE_DELIVERY'
                ,'PICKING'
                ,'ORDER_MATCH'
                ,'SHIPPING'
                )
            and id in (select laborder_id from qc_glasses_final_inspection where 
            date(convert_tz(created_at,@@session.time_zone,'+8:00'))=date('%s') and is_qualified=True)
            """ % nowtime

            sql_total = """
            select count(id) as qty from oms_laborder where (%s)
            """ % base_paras

            logging.debug(sql_total)

            sql_vd_2_4_7_8 = """
            select count(id) as qty from oms_laborder where (%s) and 
            (vendor='2' or vendor='4' or vendor ='7' or vendor ='8' )
            """ % base_paras

            sql_vd_5_6_9_10 = """
            select count(id) as qty from oms_laborder where (%s) and 
            (vendor='5' or vendor='6' or vendor='9' or vendor='10')
            """ % base_paras

            items = {}

            results = self.__get_results(sql_total)
            items["total"] = results[0].qty
            results = self.__get_results(sql_vd_2_4_7_8)
            items["vd_2_4_7_8"] = results[0].qty
            results = self.__get_results(sql_vd_5_6_9_10)
            items["vd_5_6_9_10"] = results[0].qty

            logging.debug(items)

            rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def get_today_shipped_laborders(self):
        rm = response_message()
        try:
            nowtime = timezone.now().strftime('%Y-%m-%d')
            # nowtime = '2018.12.01'
            base_paras = """
                   date(convert_tz(t0.created_at,@@session.time_zone,'+8:00'))=date('%s')
                   """ % nowtime

            sql_total = """
                   select count(t1.id) as qty 
                       from shipment_pre_delivery t0
                       left join shipment_pre_delivery_line t1
                       on t0.id = t1.pre_delivery_entity_id
                       left join oms_laborder lbo
                       on t1.lab_order_entity_id=lbo.id 
                       where (%s)
                   """ % base_paras

            logging.debug(sql_total)

            sql_vd_2_4_7_8 = """
                   select count(t1.id) as qty 
                       from shipment_pre_delivery t0
                       left join shipment_pre_delivery_line t1
                       on t0.id = t1.pre_delivery_entity_id 
                       left join oms_laborder lbo
                       on t1.lab_order_entity_id=lbo.id 
                       where (%s) and 
                   (lbo.vendor='2' or lbo.vendor='4' or lbo.vendor ='7' or lbo.vendor ='8')
                   """ % base_paras

            sql_vd_5_6_9_10 = """
                   select count(t1.id) as qty 
                       from shipment_pre_delivery t0
                       left join shipment_pre_delivery_line t1
                       on t0.id = t1.pre_delivery_entity_id 
                       left join oms_laborder lbo
                       on t1.lab_order_entity_id=lbo.id 
                       where (%s) and 
                   (lbo.vendor='5' or lbo.vendor='6' or lbo.vendor ='9' or lbo.vendor ='10')
                   """ % base_paras

            sql_holded = """
                   select count(t1.id) as qty 
                       from shipment_pre_delivery t0
                       left join shipment_pre_delivery_line t1
                       on t0.id = t1.pre_delivery_entity_id
                       left join oms_laborder lbo
                       on t1.lab_order_entity_id=lbo.id 
                       where (%s) and lbo.status ='ONHOLD'
                   """ % base_paras

            sql_canceled = """
                    select count(t1.id) as qty 
                        from shipment_pre_delivery t0
                        left join shipment_pre_delivery_line t1
                        on t0.id = t1.pre_delivery_entity_id 
                        left join oms_laborder lbo
                        on t1.lab_order_entity_id=lbo.id 
                        where (%s) and lbo.status ='CANCELLED'
                    """ % base_paras

            items = {}

            results = self.__get_results(sql_total)
            items["total"] = results[0].qty
            results = self.__get_results(sql_vd_2_4_7_8)
            items["vd_2_4_7_8"] = results[0].qty
            results = self.__get_results(sql_vd_5_6_9_10)
            items["vd_5_6_9_10"] = results[0].qty
            results = self.__get_results(sql_holded)
            items["holded"] = results[0].qty
            results = self.__get_results(sql_canceled)
            items["canceled"] = results[0].qty

            logging.debug(items)

            rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def __get_results(self, sql_script):
        with connections['default'].cursor() as cursor:
            sql = sql_script
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
        return results


from django.contrib import admin


class customize_report_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'group',
        'index',
        'code',
        'name',
        'parameters_sample',
        'is_need_parameters',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'code',
        'name',
    ]

    list_filter = (
        'group',
        'is_need_parameters',
        'created_at',
        'updated_at',
    )


class PgOrderProcessingReport(base_type):
    class Meta:
        db_table = 'report_pgorder_processing_efficiency'

    report_year = models.CharField(u'Report Year', max_length=128, default='', null=True, blank=True)
    report_month = models.CharField(u'Report Month', max_length=128, default='', null=True, blank=True)
    report_day = models.CharField(u'Report Day', max_length=128, default='', null=True, blank=True)
    entity_id = models.CharField(u'Entity_Id', max_length=128, default='', null=True, blank=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    order_datetime = models.CharField(u'Order Datetime', max_length=128, default='', null=True, blank=True)
    pg_created_at = models.DateTimeField(u'Pg Created At', null=True, blank=True)
    lab_created_at = models.DateTimeField(u'Lab Created At', null=True, blank=True)
    diff_hours = models.CharField(u'Diff Hours', max_length=128, default='', null=True, blank=True)
    hold_hours = models.CharField(u'Hold Hours', max_length=128, default='', null=True, blank=True)
    status_c = models.CharField(u'Status C', max_length=128, default='', null=True, blank=True)


class PgOrderProcessingReportController:
    def generate_inlab_report(self, start_date=None, end_date=None):
        with connections['pg_oms_query'].cursor() as cursor:
            sql = """
            select * from oms_pgorder where `status`!='canceled' and
             `status`!='closed' and is_enabled=True and is_generated_report_efficiency=False
             and is_inlab=True
            """
            if start_date and end_date:
                ext_conditions = " and date(create_at)>=date('%s') and date(create_at)<=date('%s')"
                ext_conditions = ext_conditions % (start_date, end_date)
                sql = sql + ext_conditions

            logging.debug(sql)
            cursor.execute(sql)
            pgorderitems = namedtuplefetchall(cursor)
            self.__generate_inlab_report(pgorderitems)

    def __generate_inlab_report(self, pgorderitem):
        rm = response_message()
        try:
            for pgorder in pgorderitem:
                end = pgorder.create_at.strftime('%Y-%m-%d %H:%M:%S')
                d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                report_year = d2.year
                report_month = d2.month
                report_day = d2.day
                self.generate_lab(pgorder, report_year, report_month, report_day)
        except Exception as e:
            rm.capture_execption(e)
            logging.critical(e)
            logging.debug('Exception: %s' % e)
            return rm

    def generate_lab(self, pgorder, report_year, report_month, report_day):
        logging.debug(pgorder.order_number)
        pg_item = PgOrderItem.objects.filter(order_number=pgorder.order_number)[0]
        lbs = LabOrder.objects.filter(lab_number=pg_item.lab_order_number)
        if len(lbs) > 0:
            lb = lbs[0]

            pgorder_report = PgOrderProcessingReport()
            pgorder_report.report_year = report_year
            pgorder_report.report_month = report_month
            pgorder_report.report_day = report_day
            pgorder_report.order_number = pgorder.order_number
            pgorder_report.order_datetime = pgorder.order_datetime
            pgorder_report.pg_created_at = pgorder.create_at
            pgorder_report.status_c = pgorder.status_control
            pgorder_report.entity_id = pgorder.id
            pgorder_report.lab_created_at = lb.create_at
            # pg到lab时间差
            pgorder_report.diff_hours = self.diff_hours(pgorder.create_at, lb.create_at)
            # lab到hold时间差
            hold_time = self.get_hold_time(lb.id)
            if hold_time <> '':
                pgorder_report.hold_hours = hold_time

            pg = PgOrder.objects.get(order_number=pgorder_report.order_number)
            pg.is_generated_report_efficiency = True
            pg.save()
            pgorder_report.save()

            logging.debug("----is finish----")

    # pg到lab时间差
    def diff_hours(self, pg_time, lab_time):
        start = pg_time.strftime("%Y-%m-%d %H:%M:%S")
        end = lab_time.strftime('%Y-%m-%d %H:%M:%S')
        d1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        delta = d2 - d1
        hours = float(delta.seconds) / 3600
        days = delta.days
        if days > 0:
            hours_tmp = float(days) * 24
            hours = float(hours_tmp) + float(hours)
            hours = '%.1f' % hours
        hours = decimal.Decimal(hours)
        hours = '%.1f' % hours
        return hours

    # 获取hold时间
    def get_hold_time(self, id):
        hold_time = ''
        unhold_time = ''
        lab_hold = OperationLog.objects.filter(object_entity=id, action='Hold')
        lab_unhold = OperationLog.objects.filter(object_entity=id, action='Unhold')
        logging.debug(lab_hold)
        logging.debug(lab_unhold)
        if len(lab_hold) > 0:
            hold_time = lab_hold[0].created_at
            logging.debug(hold_time)
        if len(lab_unhold) > 0:
            unhold_time = lab_unhold[0].created_at
            logging.debug(unhold_time)

        if hold_time <> '' and unhold_time <> '':
            start = hold_time.strftime("%Y-%m-%d %H:%M:%S")
            end = unhold_time.strftime('%Y-%m-%d %H:%M:%S')
            d1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            delta = d2 - d1
            hours = float(delta.seconds) / 3600
            days = delta.days
            if days > 0:
                hours_tmp = float(days) * 24
                hours = float(hours_tmp) + float(hours)
            hours = '%.1f' % hours
            hours = decimal.Decimal(hours)
            return hours

    # 根据时间段生成报表
    def generate_pgorder_report_bydate(self, start_date=None, end_date=None):
        rm = response_message()
        try:
            with connections['pg_oms_query'].cursor() as cursor:
                sql = """
                select * from oms_pgorder, where `status`!='canceled' and `status`!='closed' and is_enabled=True
                and is_inlab=False 
                """
                ext_conditions = " and date(create_at)>=date('%s') and date(create_at)<=date('%s')"
                if start_date and end_date:
                    ext_conditions = ext_conditions % (start_date, end_date)
                    sql = sql + ext_conditions

                logging.debug(sql)
                cursor.execute(sql)
                pgorderitems = namedtuplefetchall(cursor)
                if len(pgorderitems) == 0:
                    rm.code = 0
                    rm.message = '暂无' + start_date + "至" + end_date + "数据"
                    return rm

                for pgorder in pgorderitems:
                    end = pgorder.create_at.strftime('%Y-%m-%d %H:%M:%S')
                    d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                    report_year = d2.year
                    report_month = d2.month
                    report_day = d2.day
                    self.generate_not_in_lab(pgorder, report_year, report_month, report_day)

                rm.code = 0
                rm.message = '报表已生成'
                return rm

        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)
        return rm


class LabOrderProductionReport(base_type):
    class Meta:
        db_table = 'report_laborder_production_efficiency'

    report_year = models.CharField(u'Report Year', max_length=128, default='', null=True, blank=True)
    report_month = models.CharField(u'Report Month', max_length=128, default='', null=True, blank=True)
    report_day = models.CharField(u'Report Day', max_length=128, default='', null=True, blank=True)
    entity_id = models.CharField(u'Entity_Id', max_length=128, default='', null=True, blank=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    order_datetime = models.CharField(u'Order Datetime', max_length=128, default='', null=True, blank=True)
    vendor = models.CharField(u'Vendor', max_length=128, default='', null=True, blank=True)
    lens_type = models.CharField(u'Lens Type', max_length=128, default='', null=True, blank=True)
    lab_created_at = models.DateTimeField(u'Lab Created At', null=True, blank=True)
    ship_created_at = models.DateTimeField(u'Ship Created At', null=True, blank=True)
    diff_hours = models.DecimalField(u'Diff Hours', max_digits=8, decimal_places=1, default=0)
    hold_hours = models.DecimalField(u'Hold Hours', max_digits=8, decimal_places=1, default=0)
    diff_hours_truly = models.DecimalField(u'Diff Hours Truly', max_digits=8, decimal_places=1, default=0)
    diff_level = models.CharField(u'Diff Level', max_length=128, default='', null=True, blank=True)


class LabOrderProductionReportController:
    def generate_production_report(self, start_date=None, end_date=None):
        rm = response_message()
        try:
            #
            # 2019.10.01 by guof
            # 调整计算方式:采用每次限定100条记录，间隔5秒，确保资源不被无限制抢占
            #
            lbos = LabOrder.objects.filter(is_generated_production_report=False)
            lbos_count = lbos.count()

            logging.critical("There is [%s] record in todo list ." % lbos_count)

            calculate_times = int(lbos_count / 100) + 1
            max_id = 0
            for idx in range(1, calculate_times):
                logging.critical("Current Index [%s]/[%s] ...." % (idx, calculate_times))
                try:

                    with connections['pg_oms_query'].cursor() as cursor:
                        sql = """
                        select * from oms_laborder 
                        where lab_number not like '%%R%%' 
                        and is_enabled=True and is_generated_production_report=False
                        and id > %d
                        order by id
                        limit 100
                        """

                        logging.critical(sql)

                        sql = sql % max_id
                        logging.critical(sql)
                        cursor.execute(sql)
                        logging.critical('excuted')
                        lbo_items = namedtuplefetchall(cursor)
                        logging.critical('namedtuplefetchall')
                        if lbo_items:
                            items_count = len(lbo_items)
                            max_id = lbo_items[items_count - 1].id
                            logging.critical('max id: %s' % max_id)

                        logging.critical('lbo items start ---->')
                        for lbo in lbo_items:
                            logging.critical("Current Lab Order [%s][%s] ...." % (lbo.id, lbo.lab_number))
                            end = lbo.create_at.strftime('%Y-%m-%d %H:%M:%S')
                            d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                            report_year = d2.year
                            report_month = d2.month
                            report_day = d2.day
                            logging.critical(d2.day)
                            self.generate_ship_report(lbo, report_year, report_month, report_day)
                            logging.critical('generate_ship_report')

                except Exception as ex:
                    logging.critical('generate_production_report: %s' % str(ex))
                finally:
                    connections['pg_oms_query'].close()
                    logging.critical('Explicit Closed the db connection ....')

                logging.critical("Wait for next loop .... you can canceled in this cycle.")
                for tm in range(1, 6):
                    time.sleep(1)
                    logging.critical('wait for [%s] ....' % tm)
        except Exception as e:
            rm.capture_execption(e)
            logging.critical(e)
            logging.debug('Exception: %s' % e)
            return rm

    def get_lens_type(self, vendor):
        lens_type = 'stock_lens'
        if vendor == '4' or vendor == '5' or vendor == '9':
            lens_type = 'rx_lens'
        elif vendor == '7':
            lens_type = 'tint_lens'
        return lens_type

    def get_diff_level(self, lens_type, diff_hours):
        diff_level = '4.Unshipped'
        if diff_hours == 0.0:
            return diff_level
        if lens_type == 'rx_lens' or lens_type == 'tint_lens':
            if diff_hours <= 48.0:
                diff_level = '1.Qualified'
            elif diff_hours > 48.0 and diff_hours <= 72.0:
                diff_level = '2.Unqualified'
            else:
                diff_level = '3.Overdue'
        elif lens_type == 'stock_lens':
            if diff_hours <= 24.0:
                diff_level = '1.Qualified'
            elif diff_hours > 24.0 and diff_hours <= 48.0:
                diff_level = '2.Unqualified'
            else:
                diff_level = '3.Overdue'
        return diff_level

    def generate_ship_report(self, lb, report_year, report_month, report_day):
        # lb = LabOrder.objects.get(lab_number=lb_item.lab_number)
        try:
            try:
                lborder_report = LabOrderProductionReport.objects.get(lab_number=lb.lab_number)
            except Exception as ex:
                lborder_report = LabOrderProductionReport()
            lborder_report.report_year = report_year
            lborder_report.report_month = report_month
            lborder_report.report_day = report_day
            lborder_report.lab_number = lb.lab_number
            lborder_report.entity_id = lb.id
            lborder_report.order_datetime = lb.order_datetime
            lborder_report.vendor = lb.vendor
            lborder_report.lens_type = self.get_lens_type(lb.vendor)
            lborder_report.lab_created_at = lb.create_at
            lborder_report.diff_level = '4.Unshipped'
            lborder_report.save()

            logging.critical('start generate_ship_report .... ')

            delivey_items = pre_delivery_line.objects.filter(lab_order_entity=lb).order_by('-id')
            if delivey_items:
                logging.critical(delivey_items)
                if len(delivey_items) > 0:
                    logging.critical('ship created at ....')
                    lborder_report.ship_created_at = delivey_items[0].created_at
                    # 拣配到lab时间差
                    diff_hours = self.diff_hours(delivey_items[0].created_at, lb.create_at)
                    lborder_report.diff_hours = diff_hours
                    lborder_report.is_generated_production_report = True

                    logging.critical('is_generated_production_report --> True')

                    # hold时间差
                    hold_time = self.get_hold_time(lb.lab_number)
                    logging.critical('######################################################################')
                    logging.critical('hold time: %s' % hold_time)
                    if hold_time > 0:
                        lborder_report.hold_hours = hold_time
                        dh_truly = float(hold_time) + float(diff_hours)
                        lborder_report.diff_hours_truly = dh_truly
                    else:
                        lborder_report.diff_hours_truly = lborder_report.diff_hours

                    logging.critical('no go to diff_level')
                    logging.critical('----------------------------------------------------------------------')
                    logging.critical('lens_type - %s' % lborder_report.lens_type)
                    logging.critical('diff_hours_truly - %s' % lborder_report.diff_hours_truly)
                    lborder_report.diff_level = self.get_diff_level(lborder_report.lens_type,
                                                                    float(lborder_report.diff_hours_truly))
                    logging.critical('----------------------------------------------------------------------')
                    lborder_report.save()

                    try:
                        with connections['default'].cursor() as cursor:
                            sql = """
                                update oms_laborder set is_generated_production_report=True where id=%d
                                """
                            sql = sql % lb.id
                            cursor.execute(sql)
                    except Exception as ex:
                        pass
                    finally:
                        connections['default'].close()
                    # lb.is_generated_production_report=True
                    # lb.save()

                    logging.critical(
                        "diff_hours [%s] [%s] ...." % (lborder_report.lab_number, lborder_report.diff_hours_truly))
                    logging.debug("-------laborder production success--------")
        except Exception as ex:
            logging.critical('self generate_ship_report: %s' % str(ex))

    # 拣配到lab时间差
    def diff_hours(self, ship_time, lab_time):
        hours = 0.0
        try:
            start = lab_time.strftime("%Y-%m-%d %H:%M:%S")
            end = ship_time.strftime('%Y-%m-%d %H:%M:%S')
            d1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            logging.debug(d1)
            logging.debug(d2)
            delta = d2 - d1
            hours = float(delta.seconds) / 3600
            days = delta.days
            if days > 0:
                hours_tmp = float(days) * 24
                hours = float(hours_tmp) + float(hours)
                hours = '%.1f' % hours
            hours = decimal.Decimal(hours)
            hours = '%.1f' % hours
        except Exception as ex:
            logging.critical('diff_hours: %s' % str(ex))
        return hours

    # 获取hold时间
    def get_hold_time(self, order_number):
        try:
            hold_time = ''
            unhold_time = ''
            lab_hold = OrderTracking.objects.filter(order_number=order_number, action='ONHOLD')
            lab_unhold = OrderTracking.objects.filter(order_number=order_number, action='CANCEL_HOLD')
            logging.debug(lab_hold)
            logging.debug(lab_unhold)
            if len(lab_hold) > 0:
                hold_time = lab_hold[0].create_at
                logging.critical(hold_time)
            if len(lab_unhold) > 0:
                unhold_time = lab_unhold[0].create_at
                logging.critical(unhold_time)

            if hold_time and unhold_time:
                start = hold_time.strftime("%Y-%m-%d %H:%M:%S")
                end = unhold_time.strftime('%Y-%m-%d %H:%M:%S')
                d1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                delta = d2 - d1
                hours = float(delta.seconds) / 3600
                days = delta.days
                if days > 0:
                    hours_tmp = float(days) * 24
                    hours = float(hours_tmp) + float(hours)
                hours = '%.1f' % hours
                hours = decimal.Decimal(hours)
                return hours

            lab_hold = OrderTracking.objects.filter(order_number=order_number, action='R2HOLD')
            lab_unhold = OrderTracking.objects.filter(order_number=order_number, action='CANCEL_HOLD')
            logging.debug(lab_hold)
            logging.debug(lab_unhold)
            if len(lab_hold) > 0:
                hold_time = lab_hold[0].create_at
                logging.critical(hold_time)
            if len(lab_unhold) > 0:
                unhold_time = lab_unhold[0].create_at
                logging.critical(unhold_time)

            if hold_time and unhold_time:
                start = hold_time.strftime("%Y-%m-%d %H:%M:%S")
                end = unhold_time.strftime('%Y-%m-%d %H:%M:%S')
                d1 = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                d2 = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                delta = d2 - d1
                hours = float(delta.seconds) / 3600
                days = delta.days
                if days > 0:
                    hours_tmp = float(days) * 24
                    hours = float(hours_tmp) + float(hours)
                hours = '%.1f' % hours
                hours = decimal.Decimal(hours)
                return hours
        except Exception as ex:
            logging.critical('hold time: %s' % str(ex))

        return 0.0


class ReportConfig(base_type):
    class Meta:
        db_table = 'report_report_config'

    name = models.CharField(u'Name', max_length=128, default='', null=True, blank=True)
    subscribe = models.CharField(u'Subscribe', max_length=521, default='', null=True, blank=True)
    comments = models.TextField(u'Comments', max_length=512, default='', null=True, blank=True)


class ReportInfo(base_type):
    class Meta:
        db_table = 'report_report_info'

    name = models.CharField(u'Name', max_length=128, default='', null=True, blank=True)
    year = models.CharField(u'Year', max_length=128, default='', null=True, blank=True)
    month = models.CharField(u'Mouth', max_length=128, default='', null=True, blank=True)
    day = models.CharField(u'Day', max_length=128, default='', null=True, blank=True)
    mold = models.CharField(u'Mold', max_length=128, default='', null=True, blank=True)
    comments = models.TextField(u'Comments', default='', blank=True, null=True)
    is_send = models.BooleanField(u'Is Send', default=False)


class ReportInfoLine(base_type):
    class Meta:
        db_table = 'report_report_info_line'

    base_entity = models.CharField(u'Base Entity', max_length=128, default='', null=True)
    item = models.CharField(u'Item', max_length=128, default='', null=True)
    quantity = models.CharField(u'Quantity', max_length=128, default='', null=True)


class ReportJobStage(base_type):
    class Meta:
        db_table = 'report_job_stage'

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='ORJS', editable=False)

    job_type = models.CharField(u'Job Type', max_length=20, default='ORJS', null=True, blank=True)
    stage = models.CharField(u'Stage', max_length=128, default='', null=True, blank=True)
    status = models.CharField(u'Status', max_length=128, default='', null=True, blank=True)

    u_date = models.CharField(u'UTC Date', max_length=128, default='', null=True, blank=True)
    u_time = models.CharField(u'UTC Time', max_length=128, default='', null=True, blank=True)

    bj_date = models.CharField(u'BJ Date', max_length=128, default='', null=True, blank=True)
    bj_time = models.CharField(u'BJ Time', max_length=128, default='', null=True, blank=True)
    year = models.CharField(u'Year', max_length=128, default='', null=True, blank=True)
    month = models.CharField(u'Month', max_length=128, default='', null=True, blank=True)
    day = models.CharField(u'Day', max_length=128, default='', null=True, blank=True)
    hour = models.CharField(u'Hour', max_length=128, default='', null=True, blank=True)

    quantity = models.IntegerField(u'Quantity', default=0)
