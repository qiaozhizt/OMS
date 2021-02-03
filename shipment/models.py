# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction
import logging
from util.base_type import base_type
from util.response import *
from util.db_helper import *

from oms.models.order_models import LabOrder, PgOrderItem, PgOrder
from api.controllers.tracking_controllers import tracking_lab_order_controller

from oms.models.dict_models import *
from oms.models.product_models import *
import time
import datetime
from django.utils import timezone
from django.core import serializers
from oms.models.holiday_setting_models import HolidaySetting
from django.forms import ModelForm
from util.response import response_message
from util.dict_helper import dict_helper
from util.format_helper import *
from oms.controllers.lab_order_controller import lab_order_controller
import requests
import json
from pg_oms import settings
from wms.models import inventory_struct_warehouse_controller, product_frame, locker_controller, LockersItem
from accsorder.models import AccsOrder


# Create your models here.
class address:
    pass

class StkoOrder:
    def __init__(self):
        self.quantity = 0

class reponse_order_detail:

    def __init__(self):
        self.pre_delivery_entity = None
        self.pg_order_entity = None
        self.current_lab_order_entity = None
        self.pg_order_item_entities = []
        self.lab_order_entities = []
        self.order_status = -1

    @property
    def get_items_count(self):
        count = 0
        for pi in self.pg_order_item_entities:
            count += pi.quantity

        return count

    def get_by_lab_order_entity(self, order_entity, flag='B'):
        obj = reponse_order_detail()
        try:
            if flag == 'A':
                lbo = AccsOrder.objects.get(id=order_entity)
            else:
                lbo = LabOrder.objects.get(id=order_entity)
            obj = self.__get_by_lab_order(lbo)

        except Exception as e:
            logging.debug(e.message)

        return obj

    def get_by_lab_number(self, order_number, flag='B'):
        obj = reponse_order_detail()
        try:
            if flag == 'A':
                lbo = AccsOrder.objects.get(accs_order_number=order_number)
            else:
                lbo = LabOrder.objects.get(lab_number=order_number)
            obj = self.__get_by_lab_order(lbo)

        except Exception as e:
            logging.debug(e.message)

        return obj

    def __get_by_lab_order(self, lab_order):
        obj = reponse_order_detail()
        try:
            lbo = lab_order
            obj.current_lab_order_entity = lbo
            if lbo.type == 'STKO':
                pgi_entity = lbo.base_entity
                obj.pg_order_entity = None
                lab_list = lbo.lab_number.split("-")
                quantity = ''
                for item in lab_list:
                    if 'T' in item:
                        quantity = item.split('T')[1]
                        break
                stko = StkoOrder()
                stko.quantity = int(quantity)
                obj.pg_order_item_entities.append(stko)
                lbos = LabOrder.objects.filter(order_number=lbo.order_number)
                for lb in lbos:
                    obj.lab_order_entities.append(lb)
                obj.order_status = 0
            else:
                pgi_entity = lbo.base_entity
                pgi = PgOrderItem.objects.get(id=pgi_entity)

                po = PgOrder.objects.get(order_number=pgi.order_number)
                obj.pg_order_entity = po

                pgis = PgOrderItem.objects.filter(order_number=pgi.order_number)

                for pi in pgis:
                    obj.pg_order_item_entities.append(pi)
                    lbos = LabOrder.objects.filter(base_entity=pi.id)
                    for lb in lbos:
                        obj.lab_order_entities.append(lb)

                obj.order_status = 0

        except Exception as e:
            logging.debug(e.message)

        return obj


class choices:
    DELIVERY_STATUS_CHOICES = (
        ('', 'New'),
        ('SHIPPED', 'Shipped'),
    )


class pre_delivery(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PRED', editable=False)
    status = models.CharField(u'状态', max_length=40, default='', blank=True,
                              choices=choices.DELIVERY_STATUS_CHOICES)

    current_line = None

    e_count = models.IntegerField(u'东部数量', default=0)
    w_count = models.IntegerField(u'西部数量', default=0)
    express_count = models.IntegerField(u'加急数量', default=0)
    other_count = models.IntegerField(u'未知数量', default=0)
    is_combine = models.BooleanField(u'是否点击合并操作', default=False)
    shipping_method = models.CharField(u'Shipping Method', max_length=128, default='STANDARD', blank=True, null=True)

    @property
    def lines(self):
        lines = pre_delivery_line.objects.filter(pre_delivery_entity=self)
        return lines

    @property
    def lines_sorted(self):
        lines = pre_delivery_line.objects.filter(pre_delivery_entity=self).order_by('-id')
        return lines

    @property
    def get_orders_count(self):
        data_set = set()
        orders_count = self.lines.exclude(ship_region='EMPLOYEE').values('pg_order_entity').order_by('pg_order_entity').distinct().count()
        employee_orders_count = 0
        for item in self.lines.filter(ship_region='EMPLOYEE',).values('lab_order_entity'):
            lab = LabOrder.objects.get(id=item['lab_order_entity'])
            if lab.order_number in data_set:
                continue
            employee_orders_count = employee_orders_count + 1
            data_set.add(lab.order_number)
        return orders_count + employee_orders_count

    @property
    def get_glasses_count(self):
        glasses_count = self.lines.count()
        return glasses_count

    @property
    def get_glasses_picked_count(self):
        try:
            if self.current_line == None:
                return 0
            if self.current_line.lab_order_entity.type == 'STKO':
                glasses_picked_count = self.lines.filter(
                    lab_order_entity__order_number=self.current_line.lab_order_entity.order_number).count()
            else:
                glasses_picked_count = self.lines.filter(
                    lab_order_entity__order_number=self.current_line.pg_order_entity.order_number).count()
            return glasses_picked_count
        except Exception as e:
            return -1

    @property
    def get_e_count(self):
        try:
            e_count = self.lines.filter(pg_order_entity__ship_direction='E').count()
            return e_count
        except Exception as e:
            return -1

    @property
    def get_w_count(self):
        try:
            e_count = self.lines.filter(pg_order_entity__ship_direction='W').count()
            return e_count
        except Exception as e:
            return -1

    @property
    def get_standard_count(self):
        try:
            e_count = self.lines.filter(pg_order_entity__ship_direction='STANDARD').count()
            return e_count
        except Exception as e:
            return -1

    @property
    def get_express_count(self):
        try:
            e_count = self.lines.filter(pg_order_entity__ship_direction='EXPRESS').count()
            return e_count
        except Exception as e:
            return -1

    def get_orders(self, region):
        orders = []
        for line in self.lines:
            if line.ship_region == region or line.ship_region == 'Flatrate' or line.ship_region == 'EMPLOYEE':
                order_number = line.lab_order_entity.order_number
                if not order_number in orders:
                    if "SKTO" not in order_number:
                        orders.append(order_number)

        return orders

    def get_lab_orders(self, region):
        orders = []
        for line in self.lines:
            if line.ship_region == region or line.ship_region == 'Flatrate' or line.ship_region == 'EMPLOYEE':
                orders.append(line.lab_order_entity.lab_number)

        return orders

    def get_qty_inbox_list(self, region):
        qty_inbox_list = []
        orders = self.get_orders(region)
        if orders:
            for order in orders:
                qty_inbox = {}

                qty = pre_delivery_line.objects.filter(pre_delivery_entity=self).filter(
                    pg_order_entity__order_number=order).count()

                qty_inbox['order_number'] = order
                qty_inbox['qty_inbox'] = qty

                qty_inbox_list.append(qty_inbox)
        return qty_inbox_list

    def check_orders_status(self, region):
        msg = '0'
        lbos = self.get_lab_orders(region)
        for lbo in lbos:
            obj = LabOrder.objects.get(lab_number=lbo)
            if not obj.status == 'PICKING' and not obj.status == 'BOXING':
                msg = '订单[%s]状态是[%s],只有处于已拣配&装箱状态的订单才允许发货!'
                msg = msg % (obj.lab_number, obj.get_status_display())
                return msg

        return msg


class pre_delivery_line(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PREL', editable=False)
    pre_delivery_entity = models.ForeignKey(pre_delivery, models.CASCADE,
                                            blank=True,
                                            null=True, )

    pg_order_entity = models.ForeignKey(PgOrder, models.SET_NULL,
                                        blank=True,
                                        null=True, )

    lab_order_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                         blank=True,
                                         null=True, )
    is_picked = models.BooleanField(u'Is Picked', default=False)

    ship_region = models.CharField(u'Region', max_length=20)

    # add lee 2020.9.20 增加快递字段
    ship_carrier = models.CharField(u'Carrier', max_length=32,blank=True)
    tracking_number = models.CharField(u'Tracking_number', max_length=128,blank=True)
    # end add

    is_post = models.BooleanField(u'Is Post', default=False)

    @property
    def get_relation_lab_orders(self):
        lines = []
        if self.lab_order_entity.type == 'STKO':
            lab_number = self.lab_order_entity.lab_number.split("-")
            last_part = lab_number[-1]
            part_order_number = lab_number[0] + '-' + lab_number[1]
            if 'T' in last_part:
                rlbos = LabOrder.objects.filter(order_number=self.lab_order_entity.order_number, lab_number__contains=part_order_number)
            else:
                last_quantity = lab_number[-2].split("T")[-1]
                rlbos = []
                rlbos_list = LabOrder.objects.filter(order_number=self.lab_order_entity.order_number, lab_number__contains=part_order_number)
                for item in rlbos_list:
                    item_list = item.lab_number.split("-")
                    item_part = item_list[-1]
                    if 'T' not in item_part:
                        item_quantity = item_list[-2].split("T")[-1]
                        if item_quantity == last_quantity:
                            rlbos.append(item)
            for rlbo in rlbos:
                lockersItem = LockersItem.objects.filter(lab_number=rlbo.lab_number)
                logging.debug(lockersItem)
                if len(lockersItem) > 0:
                    rlbo.locker_number = lockersItem[0].storage_location + lockersItem[0].locker_num
                lines.append({
                    "lab": rlbo,
                    "flag": 'LBO'
                })

            accs_orders = AccsOrder.objects.filter(order_number=self.lab_order_entity.order_number)
            for accs in accs_orders:
                lines.append({
                    "lab": accs,
                    "flag": 'ACCS'
                })
        else:
            rlbos = LabOrder.objects.filter(order_number=self.pg_order_entity.order_number)
            for rlbo in rlbos:
                lockersItem = LockersItem.objects.filter(lab_number=rlbo.lab_number)
                logging.debug(lockersItem)
                if len(lockersItem) > 0:
                    rlbo.locker_number = lockersItem[0].storage_location + lockersItem[0].locker_num
                lines.append({
                    "lab": rlbo,
                    "flag": 'LBO'
                })

            accs_orders = AccsOrder.objects.filter(order_number=self.pg_order_entity.order_number)
            for accs in accs_orders:
                lines.append({
                    "lab": accs,
                    "flag": 'ACCS'
                })

        return lines


class pre_delivery_controller:
    def add(self, request, rod, rx_flag='B'):
        # rod = reponse_order_detail()

        rm = response_message()

        try:
            with transaction.atomic():
                pds = pre_delivery.objects.filter(user_id=request.user.id, status='')
                pd = pre_delivery()
                pd.user_id = request.user.id
                pd.user_name = request.user.username
                count = pds.count()

                if count == 1:
                    pd = pds[0]
                    if not pd.status == '':
                        rm.code = 1
                        rm.message = '归档预发货单，仅查看'
                        rm.obj = pd
                        return rm

                if count > 1:
                    rm.code = -2
                    rm.message = '发现多个未清预发货单，请先执行发货!'
                    return rm

                pd.save()
                # 订单状态验证
                # 仅能将 装配/终检合格/订单配对的状态的订单，预发货
                # 其他状态，显示当前状态，报警&阻止生成
                if rx_flag == 'A':
                    accs = AccsOrder.objects.get(id=rod.current_lab_order_entity.id)
                    logging.debug(accs.status)

                    if not accs.status == 'Packed' and not accs.status == 'Shipped':
                        rm.code = -3
                        rm.message = 'ACCS Order只有[Packed][Shipped]状态的订单允许发货! 当前状态是: %s' % accs.get_status_display()
                        return rm

                    lbovs = LabOrder.objects.filter(order_number=accs.order_number)
                    lbov = lbovs[0]
                    logging.debug(lbov.status)
                    lab_order_entity = lbov
                else:
                    lbov = LabOrder.objects.get(id=rod.current_lab_order_entity.id)
                    logging.debug(lbov.status)
                    lab_order_entity = rod.current_lab_order_entity

                if not lbov.status == 'PRE_DELIVERY' and not lbov.status == 'PICKING' \
                        and not lbov.status == 'ORDER_MATCH' and not lbov.status == 'COLLECTION':
                    rm.code = -3
                    rm.message = '只有[归集][预发货][已拣配][订单配对]状态的订单允许发货! 当前状态是: %s' % lbov.get_status_display()
                    return rm

                pdl = pre_delivery_line()

                pdls = pre_delivery_line.objects.filter(lab_order_entity=lab_order_entity,
                                                        pre_delivery_entity=pd)

                rod.pre_delivery_entity = pd
                rm.obj = pd
                pdls_count = pdls.count()
                if pdls_count > 0:
                    pdl = pdls[0]
                    rm.code = 1
                    rm.message = '重复扫描!'
                    pd.current_line = pdl

                    return rm
                else:
                    if lbov.type == 'STKO':
                        pdl.ship_region = lbov.ship_direction
                    else:
                        pdl.ship_region = rod.pg_order_entity.ship_region

                    if pdl.ship_region == 'E':
                        pd.e_count += 1
                    elif pdl.ship_region == 'W':
                        pd.w_count += 1
                    elif pdl.ship_region == 'Express':
                        pd.express_count += 1
                    else:
                        pd.other_count += 1

                    pd.save()

                logging.debug('pg order entity: %s' % rod.pg_order_entity)
                if lbov.type == 'STKO':
                    pdl.pre_delivery_entity = pd
                    pdl.pg_order_entity = None
                    pdl.lab_order_entity = rod.current_lab_order_entity
                    pdl.is_picked = True
                    pdl.ship_region = lbov.ship_direction
                    pdl.save()
                    pd.current_line = pdl
                    # 更新状态
                    lbo = pdl.lab_order_entity

                    if not lbo.status == 'PICKING':
                        lbo.status = 'PICKING'
                        lbo.save()
                        tloc = tracking_lab_order_controller()
                        tloc.tracking(lbo, request.user, 'PICKING')

                else:
                    if rod.pg_order_entity:
                        pdl.pre_delivery_entity = pd
                        pdl.pg_order_entity = rod.pg_order_entity
                        pdl.lab_order_entity = rod.current_lab_order_entity
                        pdl.is_picked = True
                        pdl.ship_region = rod.pg_order_entity.ship_region
                        pdl.save()
                        pd.current_line = pdl

                        # 更新状态
                        lbo = pdl.lab_order_entity

                        if not lbo.status == 'PICKING':
                            lbo.status = 'PICKING'
                            lbo.save()
                            tloc = tracking_lab_order_controller()
                            tloc.tracking(lbo, request.user, 'PICKING')

                rm.obj = pd

        except Exception as e:
            rm.capture_execption(e)
            logging.debug(e.message)

        return rm

    def convert(self, request):
        rm = response_message()
        entity = request.POST.get('entity', 0)
        line_id = request.POST.get('line_id', 0)
        conv = request.POST.get('convert', '')
        try:
            with transaction.atomic():
                pd = pre_delivery.objects.get(id=entity)
                pdl = pre_delivery_line.objects.get(id=line_id)
                pd.current_line = pdl

                if conv == 'EXPRESS':

                    if pdl.ship_region == 'Express' or pdl.ship_region == 'Others':
                        rm.code = -2
                        rm.message = '(-1) 加急或批量订单无法转加急!'
                        return rm

                    if pdl.ship_region == 'E':
                        e_count = pd.e_count - 1
                        if e_count < 0:
                            e_count = 0
                        pd.e_count = e_count
                    elif pdl.ship_region == 'W':
                        w_count = pd.w_count - 1
                        if w_count < 0:
                            w_count = 0
                        pd.w_count = w_count

                    pd.current_line.lab_order_entity.act_ship_direction = 'EXPRESS'
                    pd.current_line.lab_order_entity.save()
                    pd.express_count += 1
                    pd.save()

                    pdl.ship_region = 'Express'
                    pdl.save()

                    lbo = pdl.lab_order_entity

                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'CONVERT_EXPRESS', '转加急')

                elif conv == 'STANDARD':
                    if pdl.ship_region == 'E' or pdl.ship_region == 'W' or pdl.ship_region == 'Others':
                        rm.code = -2
                        rm.message = '(-1) 普通或批量订单无法转普通!'
                        return rm

                    if pdl.pg_order_entity.ship_region == 'E':
                        pd.e_count += 1
                        pdl.ship_region = 'E'
                    elif pdl.pg_order_entity.ship_region == 'W':
                        pd.w_count += 1
                        pdl.ship_region = 'W'
                    else:
                        rm.code = -3
                        rm.message = '(-3) 该订单原配送方式不是普通，不支持转普通'
                        return rm

                    pdl.save()

                    pd.current_line.lab_order_entity.act_ship_direction = 'STANDARD'
                    pd.current_line.lab_order_entity.save()

                    express_count = pd.express_count - 1
                    if express_count < 0:
                        express_count = 0
                    pd.express_count = express_count
                    pd.save()

                    lbo = pdl.lab_order_entity

                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'CONVERT_STANDARD', '加急转普通')

                elif conv == 'E':
                    if pdl.ship_region == 'Others' or pdl.ship_region == 'Express' or pdl.ship_region == 'E':
                        rm.code = -2
                        rm.message = '(-2) 批量、加急或东部订单无法转为东部发货!'
                        return rm

                    pd.e_count += 1
                    w_count = pd.w_count - 1
                    if w_count < 0:
                        w_count = 0
                    pd.w_count = w_count
                    pdl.ship_region = 'E'

                    pdl.save()
                    pd.save()

                    lbo = pdl.lab_order_entity
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'CONVERT_%s' % conv, '发货方向改为%s' % conv)

                elif conv == 'W':
                    if pdl.ship_region == 'Others' or pdl.ship_region == 'Express' or pdl.ship_region == 'W':
                        rm.code = -2
                        rm.message = '(-2) 批量、加急或西部订单无法转为西部发货!'
                        return rm
                    e_count = pd.e_count - 1
                    if e_count < 0:
                        e_count = 0
                    pd.e_count = e_count
                    pd.w_count += 1
                    pdl.ship_region = 'W'

                    pdl.save()
                    pd.save()

                    lbo = pdl.lab_order_entity
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'CONVERT_%s' % conv, '发货方向改为%s' % conv)

                return rm

        except Exception as e:
            rm.capture_execption(e)
            return rm

    def set_shipping_method(self, request, context=None):
        rm = response_message()
        entity = request.POST.get('entity', 0)
        shipping_method = request.POST.get('shipping_method')
        try:
            with transaction.atomic():
                pd = pre_delivery.objects.get(id=entity)
                pd.shipping_method = shipping_method
                logging.debug(shipping_method)
                pd.save()
        except Exception as ex:
            rm.capture_execption(ex)

        return rm


# glasses models
class documents_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='DOCB', editable=False)

    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)
    lab_order_entity = models.CharField(u'Lab Order Entity', max_length=128, default='', null=True)
    lab_number = models.CharField(u'Lab Order Number', max_length=128, default='', null=True)
    status = models.CharField(u'Status', max_length=128, null=True, blank=True, default='')
    base_entity = models.CharField(u'Base Entity', max_length=128, default='', null=True)


class received_glasses(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='REVG', editable=False)
    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)


class received_glasses_control:
    def add(self,
            request,
            lab_order_entity,
            ):
        rm = response_message()
        rm.message = '此操作已成功'

        try:
            logging.debug('开始进入 ...')
            with transaction.atomic():
                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_order_entity)

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]

                if not lbo == None:
                    objs = received_glasses.objects.all().order_by('-id')[:1]
                    if len(objs) > 0:
                        ob = objs[0]
                        if ob.lab_number == lbo.lab_number:
                            rm.code = -3
                            rm.message = '疑似重复操作'
                            return rm

                    if not lbo.status == 'FINAL_INSPECTION_YES' and not lbo.status == 'COLLECTION':
                        rm.code = -4
                        rm.message = '该订单当前状态{%s}不能更改为预发货' % lbo.get_status_display()
                        return rm

                    rg = received_glasses()
                    rg.lab_order_entity = lbo.id
                    rg.lab_number = lbo.lab_number
                    rg.user_id = request.user.id
                    rg.user_name = request.user.username
                    rg.save()

                    # 修改归集单状态
                    if lbo.status == 'COLLECTION':

                        cgs = collection_glasses.objects.filter(lab_number=lbo.lab_number)
                        if len(cgs) > 0:
                            cg = cgs[0]
                            cg.status = 'ARRIVE'
                            cg.save()
                    # 修改工厂订单状态
                    lbo.status = 'PRE_DELIVERY'
                    lbo.save()

                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'PRE_DELIVERY')
                    rm.obj = rg



                else:
                    rm.code = -4
                    rm.message = '订单未找到'
                    return rm

        except Exception as e:
            logging.debug(e.message)
            rm.capture_execption(e)

        return rm


class glasses_box(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OBOX', editable=False)
    cur_bag_id = models.CharField(u'CUR BAG ID', max_length=128, default='', null=True)
    box_id = models.CharField(u'Box ID', max_length=128, default='', blank=True, null=True)
    box_id_1 = models.CharField(u'Box ID 1', max_length=128, default='', blank=True, null=True)
    tracking_number = models.CharField(u'Tracking Number', max_length=1024, default='', blank=True, null=True)
    carrier = models.CharField(u'Carrier', max_length=128, default='', blank=True, null=True)
    region = models.CharField(u'Region', max_length=128, default='', blank=True, null=True)
    shipping_method = models.CharField(u'Shipping Method', max_length=128, default='', blank=True, null=True)


class glasses_box_item(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='BOXI', editable=False)
    box_id = models.CharField(u'BOX ID', max_length=128, default='', null=True)
    bag_id = models.CharField(u'BAG ID', max_length=128, default='', null=True)

    order_number = models.CharField(u'Order Number', max_length=128, default='', blank=True, null=True)
    order_entity = models.CharField(u'Order Entity', max_length=128, default='', blank=True, null=True)
    lab_order_entity = models.CharField(u'Lab Order Entity', max_length=128, default='', blank=True, null=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', blank=True, null=True)
    ship_direction = models.CharField(u'Ship Direction', max_length=40, default='STANDARD',blank=True, null=True)
    act_ship_direction = models.CharField(u'ACT Ship Direction', max_length=40, default='STANDARD', blank=True,null=True)

    item_id = models.CharField(u'Item ID', max_length=128, default='', blank=True, null=True)
    product_id = models.CharField(u'Product ID', max_length=128, default='', blank=True, null=True)
    frame = models.CharField(u'Frame', max_length=128, default='', blank=True, null=True)
    lab_frame = models.CharField(u'Lab Frame', max_length=128, default='', blank=True, null=True)
    customer_id = models.CharField(u'Customer ID', max_length=128, default='', blank=True, null=True)

    billing_address_id = models.CharField(u'Billing Address ID', max_length=128, default='', blank=True, null=True)
    shipping_address_id = models.CharField(u'Shipping Address ID', max_length=128, default='', blank=True, null=True)
    firstname = models.CharField(u'First Name', max_length=128, default='', blank=True, null=True)
    lastname = models.CharField(u'Last Name', max_length=128, default='', blank=True, null=True)
    name = models.CharField(u'Name', max_length=50, null=True, blank=True)
    street1 = models.CharField(u'Street1', max_length=255, null=True, blank=True)
    street2 = models.CharField(u'Street2', max_length=255, null=True, blank=True)
    city = models.CharField(u'City', max_length=30, null=True, blank=True)
    state = models.CharField(u'State', max_length=30, null=True, blank=True)
    zip = models.CharField(u'Zip', max_length=20, null=True, blank=True)
    country = models.CharField(u'Country', max_length=2, default='US', null=True, blank=True)
    phone = models.CharField(u'Phone', max_length=20, blank=True)
    instruction = models.CharField(u'Instruction', max_length=512, default='', blank=True, null=True)
    comments_ship = models.CharField(u'Comments Ship', max_length=128, default='', blank=True, null=True)
    tracking_code = models.CharField(u'Tracking Code', max_length=128, default='', blank=True, null=True)

    # 地址校验标识
    is_issue_addr = models.BooleanField(u'Is Issue Address', default=False)
    is_verified_addr = models.BooleanField(u'Is Verified Address', default=False)

    # add lee 2020.9.20 增加快递字段
    ship_carrier = models.CharField(u'Carrier', max_length=32,blank=True)
    tracking_number = models.CharField(u'Tracking_number', max_length=128,blank=True)
    # end add

class glasses_box_bag(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OGBB', editable=False)
    bag_id = models.CharField(u'BAG ID', max_length=128, default='', null=True)
    quantity = models.IntegerField(u'Quantity', default=0)


# Shipment History
class ShipmentHistory(base_type):
    class Meta:
        db_table = "shipment_shipping_history"

    ACTION_CHOICES = (
        ('BUY', 'Buy'),
        ('REFUND', 'Refund'),
    )
    # 此表于19.09.21创建，基于SHIPMENT系统的原表新增了几个字段
    type = models.CharField(u'Type', max_length=20, default='OSHH', editable=False)
    # 较原表新增字段------start
    order_number = models.CharField(u'Order Number', max_length=128, default='', blank=True, null=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', blank=True, null=True)
    box_created_at = models.CharField(max_length=50, default='', null=True, blank=True)
    shipment_created_at = models.CharField(max_length=50, default='', null=True, blank=True)
    # 较原表新增字段-------end
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default='', null=True, blank=True)
    shipment_entity = models.CharField(max_length=50, default='', null=True, blank=True)
    shipping_id = models.CharField(max_length=50, default='', null=True, blank=True)
    shipping_from = models.CharField(max_length=512, default='', null=True, blank=True)
    shipping_to = models.CharField(max_length=512, default='', null=True, blank=True)

    ep_id = models.CharField(max_length=128, default='', null=True, blank=True)
    ep_reference = models.CharField(max_length=512, default='', null=True, blank=True)
    ep_status = models.CharField(max_length=512, default='', null=True, blank=True)
    ep_refund_status = models.CharField(max_length=512, default='', null=True, blank=True)
    ep_batch_id = models.CharField(max_length=512, default='', null=True, blank=True)
    ep_tracking_code = models.CharField(max_length=512, default='', null=True, blank=True)
    ep_label_url = models.CharField(max_length=2048, default='', null=True, blank=True)
    ep_public_url = models.CharField(max_length=2048, default='', null=True, blank=True)

    ep_is_return = models.CharField(max_length=50, default='', null=True, blank=True)

    ep_fees = models.CharField(max_length=2048, default='', null=True, blank=True)
    ep_selected_rate = models.TextField(default='', null=True, blank=True)
    ep_postage_weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ep_service = models.CharField(max_length=50, null=True, blank=True)

    ep_postage_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ep_label_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ep_bill_amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    ep_created_at = models.CharField(max_length=50, default='', null=True, blank=True)
    ep_updated_at = models.CharField(max_length=50, default='', null=True, blank=True)


class glasses_box_bag_controller:
    def create_bag(self, parameters):
        rm = response_message()
        try:
            box_id = parameters.get('box_id', '')
            user_id = parameters.get('user_id', '')
            user_name = parameters.get('user_name', '')
            gbb = glasses_box_bag()
            gbb.base_entity = box_id
            gbb.user_id = user_id
            gbb.user_name = user_name
            gbb.save()

            gbb.bag_id = gbb.id
            gbb.save()

            data = {}
            data['gbb_id'] = gbb.bag_id
            rm.obj = data

            logging.debug('bag create ....')

        except Exception as ex:
            rm.capture_execption(ex)

        return rm


class glasses_box_controller:
    def add(self, request, data_dict=None):
        rm = response_message()
        try:
            isVerificationState = True
            if request:
                pd_entity = request.GET.get('pd_entity', '')
                lab_order_entity = request.GET.get('lab_order_entity', '')
                user_id = request.user.id
                user_name = request.user.username
            else:
                isVerificationState = False
                pd_entity = data_dict.get('pd_entity', '')
                lab_order_entity = data_dict.get('lab_order_entity', '')
                user_id = 0
                user_name = "System"

            if not pd_entity or pd_entity == '0':
                rm.code = 5
                rm.message = '对应的BOX ID不正确'

            pdl = pre_delivery.objects.get(id=pd_entity)

            if not pdl.status == '' and pdl.status is not None and isVerificationState:
                rm.code = 6
                rm.message = '对应的BOX 状态必须 是打开的状态'

            pd = pre_delivery.objects.get(id=pd_entity)

            data = {}
            rm.obj = data
            # if not pdl.is_combine:
            #     rm.code = 444
            #     rm.message = '请到已拣配详情页点击计算合并发货按钮'
            #     return rm

            data['box_id'] = pd_entity
            data['order_count'] = pd.get_orders_count
            data['glasses_count'] = pd.get_glasses_count

            data['bag_id'] = 0
            data['bag_count'] = 0
            data['bag_cur'] = 0

            data['scaned_count'] = 0

            rm.obj = data

            if not lab_order_entity:
                rm.code = 0
                return rm

            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_order_entity)

            lbo = None

            if len(lbos) > 0:
                lbo = lbos[0]

            if not lbo:
                rm.code = 555
                rm.message = '没有找到对应的Lab Order 刚才输入的参数:[%s]' % lab_order_entity
                return rm

            if not lbo.status == 'PICKING' and not lbo.status == 'BOXING' and isVerificationState:
                rm.code = 666
                rm.message = '工厂订单[%s]当前状态[%s]不是已拣配，不支持装箱操作' % (lbo.lab_number, lbo.status)
                return rm

            if lbo.status == 'BOXING' and lbo.lab_number == lab_order_entity:
                rm.code = 445
                rm.message = '重复扫描'
                return rm

            pdls = pre_delivery_line.objects.filter(lab_order_entity=lbo.id)
            if pdls.count() > 0:
                pdl = pdls[0]
                cur_pd_entity = pdl.pre_delivery_entity
                if int(cur_pd_entity.id) <> int(pd_entity):
                    rm.code = 999
                    rm.message = '当前工厂订单所属的BOX[%s] 与正在扫描的BOX不符' % cur_pd_entity.id
                    return rm

            data['lab_number'] = lbo.lab_number
            data['frame'] = lbo.frame
            # 获取合并发货信息 start
            # 获取合并发货信息 end
            # scan started .
            logging.debug('scan started')
            gbs = glasses_box.objects.filter(base_entity=pd_entity)

            if gbs.count() > 0:
                # get current box
                logging.debug('get current box')
                gb = gbs[0]
                logging.debug(gb.id)
                gbbs = glasses_box_bag.objects.filter(base_entity=gb.id).order_by('-id')

                if gbbs.count() > 0:
                    gbb = gbbs[0]
                    logging.debug('cur box id: %s' % gb.id)
                    logging.debug('cur bag id: %s' % gbb.bag_id)
                else:
                    gbb = self.__create_bag(gb)
            else:
                # create new
                logging.debug('create new')
                gb = glasses_box()

                gb.user_id = user_id
                gb.user_name = user_name
                gb.base_entity = pd_entity
                gb.save()

                gbb = self.__create_bag(gb)

            gb.cur_bag_id = gbb.bag_id
            gb.shipping_method = pd.shipping_method
            gb.save()
            # count glasses box line count
            logging.debug('count glasses box line count')
            gbls = glasses_box_item.objects.filter(base_entity=gb.id, lab_order_entity=lbo.id)

            if gbls.count() > 0:
                gbl = gbls[0]
            else:
                gbl = glasses_box_item()

            # set glasses box line
            logging.debug('set glasses box line')

            gbl.base_entity = gb.id
            gbl.box_id = gb.base_entity
            gbl.order_number = lbo.order_number
            gbl.lab_order_entity = lbo.id
            gbl.lab_number = lbo.lab_number
            gbl.user_id = user_id
            gbl.user_name = user_name
            gbl.ship_direction = lbo.ship_direction
            gbl.act_ship_direction = lbo.act_ship_direction

            gbl.bag_id = gbb.bag_id

            gbl.status = 'NEW'
            # add lee 2020.9.29 box_item增加快递公司
            gbl.ship_carrier=pdl.ship_carrier
            gbl.tracking_number=pdl.tracking_number
            #
            gbl.save()

            if lbo.type == 'STKO':
                gbl.order_number = lbo.order_number
                gbl.item_id = 0
                gbl.product_id = 0
                gbl.frame = lbo.frame
                gbl.lab_frame = lbo.frame
                gbl.lab_order_entity = lbo.id
                gbl.lab_number = lbo.lab_number

                gbl.order_entity = 0
                gbl.customer_id = 0
                gbl.billing_address_id = 0
                gbl.shipping_address_id = 0
                gbl.firstname = 'Katie'
                gbl.lastname = 'Himes'
                gbl.name = '%s %s' % (gbl.firstname, gbl.lastname)
                gbl.zip = '15234'
                gbl.street1 = '3843 Willow Ave #1'
                gbl.street2 = ''
                gbl.city = 'Pittsburgh'
                gbl.state = 'Pennsylvania'
                gbl.country = 'US'
                gbl.phone = '4127592912'
                gbl.instruction = ''
                gbl.comments_ship = lbo.comments_ship

                if isVerificationState:
                    gbl.status = 'NEW'
                else:
                    gbl.status = 'SHIPPED'
                    gbl.tracking_code = lbo.shipping_number

                gbl.save()
            else:
                sql = '''
                /*
                 根据工厂订单号查询发货全部信息
                */
                select 
                t0.order_number
                ,t0.item_id
                ,t0.product_id
                ,t0.frame
                ,t1.id as lab_order_entity
                ,t1.lab_number 
    
                ,t2.base_entity as order_entity
                ,t2.customer_id
                ,t2.billing_address_id
                ,t2.shipping_address_id
                ,t2.firstname
                ,t2.lastname
                ,t2.postcode
                ,t2.street
                ,t2.street2
                ,t2.city
                ,t2.region
                ,t2.country_id
                ,t2.phone
                ,t2.instruction
                ,t1.comments_ship
                from oms_pgorderitem t0
                left join oms_laborder t1
                on t0.id=t1.base_entity
                left join oms_pgorder t2
                on t0.order_number=t2.order_number
                where 
                t1.lab_number='%s'
                '''

                sql = sql % lbo.lab_number

                logging.debug(sql)
                with connections['default'].cursor() as cursor:

                    logging.info(sql)
                    cursor.execute(sql)

                    results = namedtuplefetchall(cursor)
                    if len(results) > 0:
                        rest = results[0]
                        gbl.order_number = rest.order_number
                        gbl.item_id = rest.item_id
                        gbl.product_id = rest.product_id
                        gbl.frame = rest.frame
                        gbl.lab_frame = lbo.frame
                        gbl.lab_order_entity = lbo.id
                        gbl.lab_number = lbo.lab_number

                        gbl.order_entity = rest.order_entity
                        gbl.customer_id = rest.customer_id
                        gbl.billing_address_id = rest.billing_address_id
                        gbl.shipping_address_id = rest.shipping_address_id
                        gbl.firstname = rest.firstname
                        gbl.lastname = rest.lastname
                        gbl.name = '%s %s' % (gbl.firstname, gbl.lastname)
                        gbl.zip = rest.postcode
                        gbl.street1 = rest.street
                        gbl.street2 = rest.street2
                        gbl.city = rest.city
                        gbl.state = rest.region
                        gbl.country = rest.country_id
                        gbl.phone = rest.phone
                        gbl.instruction = rest.instruction
                        gbl.comments_ship = lbo.comments_ship

                        if isVerificationState:
                            gbl.status = 'NEW'
                        else:
                            gbl.status = 'SHIPPED'
                            gbl.tracking_code = lbo.shipping_number

                        gbl.save()
                    else:
                        rm.code = -55
                        rm.message = '查询订单信息时遇到异常!'
                        return rm

            # count glasses box bag quantity
            logging.debug('count glasses box bag quantity')
            gbls_count = glasses_box_item.objects.filter(base_entity=gb.id, bag_id=gbb.bag_id)
            bl_count = gbls_count.count()
            gbb.quantity = bl_count
            gbb.save()

            # 如果是普通订单，或者说是正常扫描操作，更新状态，否则状态不变更
            if isVerificationState:
                lbo.status = 'BOXING'
                lbo.save()

            tloc = tracking_lab_order_controller()
            if request:
                tloc.tracking(lbo, request.user, 'BOXING')
            else:
                tloc.tracking(lbo, None, 'BOXING')

            data['bag_id'] = gb.cur_bag_id

            bag_counts = glasses_box_bag.objects.filter(base_entity=gb.id)
            bag_curs = glasses_box_item.objects.filter(base_entity=gb.id, bag_id=gbb.bag_id)
            data['bag_count'] = bag_counts.count()
            data['bag_cur'] = bag_curs.count()

            if bag_curs.count() >= 16:
                data['need_new_bag'] = 1
            else:
                data['need_new_bag'] = 0

            data['gb_id'] = gb.id

            gbls = glasses_box_item.objects.filter(base_entity=gb.id).order_by('-updated_at')
            data['gbls'] = gbls
            data['scaned_count'] = gbls.count()
            data['shipping_method'] = pd.shipping_method

            # 2020.02.25 by guof. OMS-628
            # 增加标识，可以设置打开和关闭在OMS中是否合并发货的开关

            combined_on = False

            if combined_on:
                # 获取合并发货信息 start
                sql = """SELECT s.lab_number AS lab_number, s.box_id AS box_id,s.order_number as order_number,
                                 o.`status` AS lab_status, o.vendor AS vendor, s.combined_number AS combined_number
                          FROM shipment_combined_list AS s
                               LEFT JOIN oms_laborder AS o
                               ON s.lab_number = o.lab_number,
                               (SELECT combined_number FROM shipment_combined_list WHERE box_id=%s AND lab_number="%s") as a
                          WHERE s.box_id=%s AND s.combined_number=a.combined_number
                 """ % (pd_entity, lab_order_entity, pd_entity)
                items_list = []
                with connections['pg_oms_query'].cursor() as cursor:
                    cursor.execute(sql)
                    requests = namedtuplefetchall(cursor)
                    for item in requests:
                        items_list.append({
                            "lab_number": item.lab_number,
                            "box_id": item.box_id,
                            "lab_status": item.lab_status,
                            "vendor": item.vendor,
                            "combined_number": item.combined_number,
                            "order_number": item.order_number
                        })
                    data['combined_list'] = items_list

                    if len(items_list) > 0:
                        data['flag'] = 'true'
                    else:
                        data['flag'] = 'false'

            # 获取合并发货信息 end
            rm.obj = data

            return rm
        except Exception as ex:
            logging.debug(str(ex))
            rm.capture_execption(ex)
            return rm

    def __create_bag(self, gb):
        gbb = glasses_box_bag()
        gbb.base_entity = gb.id
        gbb.save()
        gbb.bag_id = gbb.id
        gbb.save()
        return gbb

    def post_box(self, request):
        rm = response_message()
        try:
            logging.debug('method : post_box')
            pd_entity = request.POST.get('dilivery_entity', 0)
            logging.debug('pd_entity: %s' % pd_entity)

            if not pd_entity or pd_entity == '0':
                rm.code = 5
                rm.message = '对应的BOX ID不正确'
                return rm

            gbs = glasses_box.objects.filter(base_entity=int(pd_entity))
            count = len(gbs)

            logging.debug('glasses box count: %s' % count)

            pd = pre_delivery.objects.get(id=pd_entity)

            if not count > 0:
                if pd.shipping_method == 'STANDARD':
                    rm.code = 55
                    rm.message = '没有找到装箱扫描的记录'
                    return rm
                else:
                    for item in pd.lines:
                        req_data = {}
                        req_data['pd_entity'] = pd.id
                        req_data['lab_order_entity'] = item.lab_order_entity.lab_number
                        self.add(None, req_data)

                    logging.debug('pd_entity: %s' % pd_entity)
                    gb = glasses_box.objects.get(base_entity=int(pd_entity))
                    logging.debug(gb.id)
            else:
                gb = gbs[0]

            if pd.shipping_method != 'STANDARD':
                # 2020.02.25 by guof. OMS-628
                # 增加box items count和pd lines count对比 如果不一致 中断执行
                pd_lines_count = pre_delivery_line.objects.filter(pre_delivery_entity=pd).count()
                gb_items_count = glasses_box_item.objects.filter(box_id=pd.id).count()

                if pd_lines_count != gb_items_count:
                    rm.code = -55
                    rm.message = '发货单与装箱单数量不符！ 发货单:%s 装箱单:%s 请联系IT支持!' % (pd_lines_count, gb_items_count)
                    return rm

            carrier = request.POST.get('carrier', '')
            tracking_number = request.POST.get('tracking_number', '')
            comments = request.POST.get('comments', '')
            region = request.POST.get('region', '')

            gb.carrier = carrier
            gb.tracking_number = tracking_number
            gb.comments = comments
            gb.region = region
            gb.box_id = gb.base_entity
            gb.box_id_1 = gb.id
            gb.save()

            data = {}
            data['box'] = dict_helper.convert_to_dict(gb)
            logging.debug('box dict: %s' % data)

            box_items = glasses_box_item.objects.filter(base_entity=gb.id)
            obis = []

            for bi in box_items:
                obis.append(bi)
            dict_obis = dict_helper.convert_to_dicts(obis)

            logging.debug(box_items.count())
            data['box_items'] = dict_obis
            # 2020.02.25 by guof. OMS-628
            # 增加标识，可以设置打开和关闭在OMS中是否合并发货的开关

            combined_on = False
            if combined_on:
                # 获取计算发货结果start
                com_list = []
                sql = """SELECT box_id,order_number,combined_number
                         FROM `shipment_combined_list`
                         WHERE box_id=%s
                         GROUP BY order_number;""" % pd_entity
                with connections['pg_oms_query'].cursor() as cursor:
                    cursor.execute(sql)
                    for item in namedtuplefetchall(cursor):
                        com_list.append({
                            "box_id": item.box_id,
                            "order_number": item.order_number,
                            "combined_number": item.combined_number
                        })

                # if len(com_list) == 0:
                #     rm.code = 444
                #     rm.message = '请点击计算合并发货'
                #     return rm

                data['combined_list'] = com_list
            # 获取计算发货结果end
            try:
                req_data = json.dumps(data, cls=DateEncoder)
                token_header = {'Content-Type': 'application/json'}
                url = settings.SHIP_ROOT_URL + settings.SHIP_PATH_POST_BOX
                logging.debug(req_data)
                res_data = requests.post(url,
                                         data=req_data,
                                         headers=token_header,
                                         timeout=120,
                                         verify=False)
                logging.debug('response data: %s' % res_data.text)
                res_json = json.loads(res_data.text)
            except  Exception as e:
                rm.code = -55
                rm.message = '请求ship2系统接口失败，请稍后重试！'
                return rm

            logging.debug('response:')
            logging.debug('----------------------------------------')
            logging.debug(res_json)

            rm.code = res_json.get('code', -1)
            rm.message = res_json.get('message', '')

            return rm
        except Exception as ex:

            logging.debug(str(ex))
            rm.capture_execption(ex)
            return rm


class collection_glasses(documents_base):
    # type类型，comments备注,send_from发出方，send_to接收方
    # 无法更新数据库
    collection_number = models.CharField(u'归集单编号', max_length=128, default='', null=True)
    type = models.CharField(u'类型', max_length=20, default='OCOL', editable=False)
    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)
    send_from = models.CharField(u'发出方', max_length=20, default='', null=True, blank=True)
    send_to = models.CharField(u'接收方', max_length=20, default='', null=True, blank=True)


class collection_glasses_control:
    def add(self, request, lab_order_entity, send_to, send_from, time_now):
        rm = response_message()
        rm.message = '此操作已成功'

        try:
            logging.debug('开始进入 ...')
            with transaction.atomic():
                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_order_entity)

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]
                # 检查订单号是有已存在于归集单列表
                if lbo is not None:
                    lab_number = lbo.lab_number
                    objs = collection_glasses.objects.all().order_by('-id')
                    if len(objs) > 0:
                        for ob in objs:
                            if ob.lab_number == lab_number:
                                rm.code = -3
                                rm.message = '该订单已经生成过归集单'
                                return rm

                    if not lbo.status == 'LENS_RECEIVE':
                        rm.code = -4
                        rm.message = '该订单当前状态{%s}不能更改为归集状态' % lbo.get_status_display()
                        return rm

                    cg = collection_glasses()
                    cg.lab_order_entity = lbo.id
                    cg.lab_number = lbo.lab_number
                    cg.status = 'IN_TRANSIT'
                    cg.user_id = request.user.id
                    cg.user_name = request.user.username
                    cg.send_from = send_from
                    cg.send_to = send_to
                    cg.collection_number = time_now
                    cg.save()

                    # lbo.status = 'COLLECTION'  # 修改lborder状态
                    # lbo.save()

                    # 改sql更新
                    with connections['default'].cursor() as c:
                        try:
                            with transaction.atomic(using='default'):
                                sql = "update oms_laborder set status='COLLECTION' where lab_number='%s'" % lab_number
                                logging.debug(sql)
                                c.execute(sql)
                        except Exception as e:
                            rm.code = -4
                            rm.message = 'sql出错:%s' % str(e)
                            return rm

                    tloc = tracking_lab_order_controller()  # 存储进订单追踪表
                    tloc.tracking(lbo, request.user, 'COLLECTION')
                    rm.obj = cg

                else:
                    rm.code = -4
                    rm.message = '订单未找到'
                    return rm

        except Exception as e:
            logging.debug(e.message)
            rm.capture_execption(e)

        return rm


class combined_list(base_type):
    box_id = models.CharField(u'Box Id', max_length=128, default='', null=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    lab_order_id = models.CharField(u'Lab Order Id', max_length=128, default='', null=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    combined_number = models.CharField(u'Combined Number', max_length=128, default='', null=True, blank=True)


class combined_list_controller:
    def check_combined(self, request):
        rm = {}
        try:
            delivery_entity = request.POST.get("dilivery_entity", "0")
            pg_dict = {}
            pg_set = set()
            if not int(delivery_entity) == 0:
                sql = """SELECT s.pre_delivery_entity_id AS box_id, p.order_number AS order_number, 
                               p.street AS street, p.region AS region, p.city AS city, p.postcode AS postcode, 
                               p.customer_name AS customer_name,l.id AS lab_id, l.lab_number AS lab_number 
                        FROM `shipment_pre_delivery_line` AS s 
                           LEFT JOIN oms_pgorder AS p 
                           ON s.pg_order_entity_id=p.id 
                           LEFT JOIN oms_laborder AS l 
                           ON s.lab_order_entity_id=l.id 
                        WHERE s.pre_delivery_entity_id=%s 
                        GROUP BY s.pg_order_entity_id""" % delivery_entity

                with connections['pg_oms_query'].cursor() as cursor:
                    cursor.execute(sql)
                    requests = namedtuplefetchall(cursor)
                    for item in requests:
                        data_list = []
                        flag = item.region + item.city + item.street + item.postcode + item.customer_name
                        if flag in pg_set:
                            pg_dict[flag].append(item.order_number)
                        else:
                            pg_set.add(flag)
                            data_list.append(item.order_number)
                            pg_dict[flag] = data_list

            combined_data_list = []
            for key,value in pg_dict.items():
                if len(value)>1:
                    combined_data_list.append({'address':key,'list':value})

            rm['code'] = 0
            rm['message'] = 'success'
            rm['obj'] = combined_data_list
            return rm
        except Exception as e:
            rm['code'] = -1
            rm['message'] = e
            return rm


class pre_trackings(models.Model):
    tracking_number = models.CharField(u'Tracking Number', max_length=1024, default='', blank=True, null=True)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)
    box_id = models.CharField(u'Box ID', max_length=128, default='', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(u'Type', max_length=20, default='TRSH', editable=False)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)


