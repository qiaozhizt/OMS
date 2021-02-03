# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction

from oms.models import LabOrder
from util.base_type import base_type
from util.response import response_message, MyException
from web_inventory import *
import re
import logging
import time
# Create your models here.
from oms.models.choices_models import *
from django.db import connections
from util.db_helper import *
import json
import datetime
#from oms.controllers.pg_order_controller import pg_order_controller
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller

# 产品基本信息姐不哦
class product_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PRDB', editable=False)

    PRODUCT_TYPE_CHOICES = (
        ('FRAME', 'Frame'),
        ('CLIPON', 'Clipon'),
        ('ACCESSORIES', 'Accessories'),
        ('LENS', 'Lens'),
        ('LABC', 'Lab Consumables'),
        ('PACM', 'Package Materials'),
        ('OFFS', 'Office Stationery'),
        ('STKG', 'Stocked Glasses'),
        ('DEVP', 'Device Parts'),
        # ('TINT', 'Tint'),
        # ('COATING', 'Coating'),
        # ('PRISM', 'Prism'),
    )

    parent = models.ForeignKey('self', models.CASCADE,
                               blank=True,
                               null=True, )

    product_type = models.CharField(u'PRODUCT TYPE', max_length=15, default='FRAME',
                                    choices=PRODUCT_TYPE_CHOICES)

    sku = models.CharField(u'SKU', max_length=40, default='', unique=True, null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    base_price = models.DecimalField(u'Base PRICE', max_digits=10, decimal_places=2, default=0)
    sku_specs = models.CharField(u'SKU 规格', max_length=128, default='', blank=True, null=True)


class warehouse(base_type):
    USER_TO_CHOICES = product_base.PRODUCT_TYPE_CHOICES
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='WARH', editable=False)
    code = models.CharField(u'Code', max_length=40)
    name = models.CharField(u'Name', max_length=256)
    location = models.CharField(u'Location', max_length=512)
    used_to = models.CharField(u'Used To', max_length=15, default='', choices=USER_TO_CHOICES)
    is_sale = models.BooleanField(u'Is Sale', default=True)

    def __str__(self):
        return self.name


class warehouse_controller:
    def get_all_frame_warehouse(self):
        items = warehouse.objects.all()
        return items


class documents_base(base_type):
    class Meta:
        abstract = True

    DOC_TYPE_CHOICES = (
        ('INIT', '库存初始化'),
        ('GENERAL_OUT', '一般类型出库'),
        ('GENERAL_IN', '一般类型入库'),
        ('REFUNDS_IN', '订单退货入库'),
        ('FAULTY', '报损出库'),
        ('STOCK_TAKING', '库存盘点差异调整'),
        ('AUTO', '系统自动'),
        ('ALLOTTED_OUT', '调拨出库'),
        ('SAMPLE_OUT', '样品出库'),
        ('ALLOTTED_IN', '调拨入库'),
        ('SAMPLE_IN', '样品入库'),

        ('ALLOCATION', '分配'),
        ('RECALL', '撤回'),
        ('NP_IN', '新品入库'),
        ('RP_IN', '补货入库'),
        ('REFUNDS_OUT', '订单退货出库')
    )

    warehouse = models.ForeignKey(warehouse, models.SET_NULL,
                                  blank=True,
                                  null=True, )

    doc_type = models.CharField(u'Doc Type', max_length=20, default='AUTO',
                                choices=DOC_TYPE_CHOICES)
    doc_number = models.CharField(u'Doc Number', max_length=40, default='', null=True, blank=True)

    status = models.CharField(u'Status', max_length=128, null=True, blank=True, default='')
    base_entity = models.CharField(u'Base Entity', max_length=128, default='', blank=True, null=True)


class customer_flatrate(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='CFOT', editable=False)
    name = models.CharField(u'Name', max_length=256)

    def __str__(self):
        return self.name


# 镜架
class product_frame(product_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PRDF', editable=False)
    FRAME_TYPE_CHOICES = (
        ('None', 'None'),
        ('Full Rim & Half Rim', 'Full Rim & Half Rim'),
        # ('FHK', 'Full Rim & Rimless (for Kids 17 and under)'),
        ('Rim Less', 'Rim Less'),
        ('Frame with Clip', 'Frame with Clip'),
        ('Goggles','Goggles'),
        ('Non-rx','Non-rx'),

    )

    FMAT_TYPE_CHOICES = (
        ('Acetate', 'Acetate'),
        ('Memory Titanium', 'Memory Titanium'),
        ('Mixed Material', 'Mixed Material'),
        ('Other Metal', 'Other Metal'),
        ('Plastic', 'Plastic'),
        ('Stainless Steel', 'Stainless Steel'),
        ('titanium', 'titanium'),
        ('TR', 'TR'),
        ('Ultem', 'Ultem'),
    )

    FSHA_TYPE_CHOICES = (
        ('Aviator', 'Aviator'),
        ('Browline', 'Browline'),
        ('Cat Eye', 'Cat Eye'),
        ('Classic Square', 'Classic Square'),
        ('Geometric', 'Geometric'),
        ('Oval', 'Oval'),
        ('Rectangle', 'Rectangle'),
        ('Round', 'Round'),
        ('Safety Glasses', 'Safety Glasses'),
        ('Square', 'Square'),
    )

    ETYP_TYPE_CHOICES = (
        ('1', '1：全框-有尖边'),
        ('2', '2：无框打孔'),
        ('3', '3：半框开槽'),
    )

    YES_OR_NO_CHOICES = (
        (0,"No"),
        (1,"Yes"),
    )

    frame_type = models.CharField(u'FRAME TYPE', max_length=20, default='NONE',
                                  choices=FRAME_TYPE_CHOICES)

    # 等同于 Frame Eyesize
    fe = models.DecimalField(u'Lens Width(mm)', max_digits=10, decimal_places=2, default=0)
    fh = models.DecimalField(u'Lens Hight(mm)', max_digits=10, decimal_places=2, default=0)
    fb = models.DecimalField(u'Frame Bridge(mm)', max_digits=10, decimal_places=2, default=0)
    ed = models.DecimalField(u'ED(mm)', max_digits=10, decimal_places=2, default=0)
    ct = models.DecimalField(u'Center thickness(mm)', max_digits=10, decimal_places=2, default=1.5)

    flatrate_customers = models.ManyToManyField(customer_flatrate, default=None, blank=True)
    web_created_at = models.DateTimeField(default=None, null=True, blank=True)
    image = models.CharField(u'Image', max_length=1024, default='', null=True, blank=True)
    thumbnail = models.CharField(u'Thumbnail', max_length=1024, default='', null=True, blank=True)
    r_a = models.DecimalField(u'R_A', max_digits=10, decimal_places=2, default=0)
    r_b = models.DecimalField(u'R_B', max_digits=10, decimal_places=2, default=0)
    r_ed = models.DecimalField(u'R_ED', max_digits=10, decimal_places=2, default=0)
    r_ed_axis = models.DecimalField(u'R_轴位', max_digits=10, decimal_places=2, default=0)
    r_circ = models.DecimalField(u'R_周长', max_digits=10, decimal_places=2, default=0)
    r_fcrv = models.DecimalField(u'R_FCRV', max_digits=10, decimal_places=2, default=0)
    r_ztilt = models.DecimalField(u'R_ZTILT', max_digits=10, decimal_places=2, default=0)
    l_a = models.DecimalField(u'L_A', max_digits=10, decimal_places=2, default=0)
    l_b = models.DecimalField(u'L_B', max_digits=10, decimal_places=2, default=0)
    l_ed = models.DecimalField(u'L_ED', max_digits=10, decimal_places=2, default=0)
    l_ed_axis = models.DecimalField(u'L_轴位', max_digits=10, decimal_places=2, default=0)
    l_circ = models.DecimalField(u'L_周长', max_digits=10, decimal_places=2, default=0)
    l_fcrv = models.DecimalField(u'L_FCRV', max_digits=10, decimal_places=2, default=0)
    l_ztilt = models.DecimalField(u'L_ZTILT', max_digits=10, decimal_places=2, default=0)
    dbl = models.DecimalField(u'DBL', max_digits=10, decimal_places=2, default=0)
    temple = models.DecimalField(u'腿长', max_digits=10, decimal_places=2, default=0)
    fmat = models.CharField(u'材质', max_length=128, null=True, blank=True, default='')
    fsha = models.CharField(u'形状', max_length=128, null=True, blank=True, default='')
    etyp = models.CharField(u'割边类型', max_length=128, null=True, blank=True, default='')
    file_path = models.CharField(u'VCA 路径', max_length=128, null=True, blank=True, default='')
    property_list = models.TextField(u'属性集合', max_length=512, default='', null=True, blank=True)
    is_activate_vca_id = models.IntegerField(u'Is Activate Vca ID', default=0)
    product_num = models.CharField(u'Product Num', max_length=128, null=True, blank=True, default='')
    attribute_set = models.IntegerField(u'属性设置',default=0)
    frame_width = models.DecimalField(u'镜架宽度', max_digits=10, decimal_places=2, default=0)

    is_nose_pad = models.IntegerField(u'Is Nose Pad',choices=YES_OR_NO_CHOICES,default=0)
    is_has_spring_hinges = models.IntegerField(u'Is Has Spring Hinges',choices=YES_OR_NO_CHOICES,default=0)
    is_color_changing = models.IntegerField(u'Is Color Changing',choices=YES_OR_NO_CHOICES,default=0)
    is_variability = models.IntegerField(u'易变形',choices=YES_OR_NO_CHOICES,default=0)
    is_already_synchronous = models.IntegerField(u'是否已经否同步',choices=YES_OR_NO_CHOICES,default=0)


# 库存结构表 - 动态生成
class inventory_struct_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='ISTB', editable=False)

    sku = models.CharField(u'SKU', max_length=40, default='', unique=True, null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)

    location = models.CharField(u'Location', max_length=128, default='', null=True, blank=True)

    # @property
    # def get_status(self):
    #     if self.name == None or self.name == '':
    #         return 'DRAFT'
    #     if self.web_women_is_in_stock or self.web_men_is_in_stock or self.web_kids_is_in_stock:
    #         return 'IN_STOCK'
    #     elif not self.web_women_is_in_stock and not self.web_men_is_in_stock and not self.web_kids_is_in_stock:
    #         return 'OUT_OF_STOCK'


# 库存结构表 - 动态生成
class inventory_struct(inventory_struct_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OIST', editable=False)
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('IN_STOCK', 'In Stock'),
        ('OUT_OF_STOCK', 'Out of stock'),
    )
    web_women_quantity = models.DecimalField(u'Web Women Quantity', max_digits=10, decimal_places=0, default=0)
    web_men_quantity = models.DecimalField(u'Web Men Quantity', max_digits=10, decimal_places=0, default=0)
    web_kids_quantity = models.DecimalField(u'Web Kids Quantity', max_digits=10, decimal_places=0, default=0)
    web_women_is_in_stock = models.BooleanField(u'Women Is In Stock', default=False)
    web_men_is_in_stock = models.BooleanField(u'Men Is In Stock', default=False)
    web_kids_is_in_stock = models.BooleanField(u'Kids Is In Stock', default=False)
    status = models.CharField(u'Status', max_length=40, default='DRAFT',
                              choices=STATUS_CHOICES)
    estimate_replenishment_date = models.DateField(u'Estimate Replenishment Date', null=True, blank=True)
    retired = models.BooleanField(u'Retired', default=False)
    lock_quantity = models.DecimalField(u'Lock Quantity', max_digits=10, decimal_places=0, default=0)
    reserve_quantity = models.DecimalField(u'Reserve Quantity', max_digits=10, decimal_places=0, default=0)
    ch_quantity = models.DecimalField(u'Channel Quantity', max_digits=10, decimal_places=0, default=0)
    al_quantity = models.DecimalField(u'Al Quantity', max_digits=10, decimal_places=0, default=0)
    web_status = models.CharField(u'Web Status', max_length=40, default='')
    web_quantity = models.DecimalField(u'Web Quantity', max_digits=10, decimal_places=0, default=0)
    oms_web_diff = models.DecimalField(u'Oms Web Diff', max_digits=10, decimal_places=0, default=0)
    last_out_of_stock= models.CharField(u'Last Out Of Stock', max_length=128, default='')
    last_in_stock= models.CharField(u'Last In Stock', max_length=128, default='')
    last_out_of_stock_date= models.CharField(u'Last Out Of Stock Date',max_length=128, default='')
    last_in_stock_date=  models.CharField(u'Last In Stock Date', max_length=128,default='')
    last_retired= models.CharField(u'Last Retired', max_length=128, default='')
    last_retired_date= models.CharField(u'Last Retired Date',max_length=128,default='')
    last_sign = models.CharField(u'Last Sign',max_length=128,default='')
    last_sign_date= models.CharField(u'Last Sign Date',max_length=128,default='')
    no_sale_quantity = models.DecimalField(u'No Sale Quantity', max_digits=10, decimal_places=0, default=0)


class inventory_struct_contoller:
    def inspection_sku(self, sku):
        rm = response_message()
        try:
            ois = inventory_struct.objects.get(sku=sku)
            rm.obj = ois
        except Exception as ex:
            rm.capture_execption(ex)

        return rm

    def add_reserver_qty(self, sku, quantity):
        rm = response_message()
        try:
            ois = inventory_struct.objects.get(sku=sku)
            ois.reserve_quantity = ois.reserve_quantity + quantity
            ois.save()
        except Exception as ex:
            logging.critical(str(ex))
            rm.capture_execption(ex)

        return rm

    def add_reserver_qty_po(self, po):
        rm = response_message()
        try:
            from oms.models.order_models import PgOrderItem
            pgis = PgOrderItem.objects.filter(pg_order_entity=po, status__in=['holded', 'pending', 'processing'])
            poc = pgorder_frame_controller()
            for pgi in pgis:
                #frame = pgi.frame[1:8]
                if pgi.attribute_set_name == 'Glasses' or pgi.attribute_set_name == 'Goggles':
                    res_rm = poc.get_lab_frame({"pg_frame": pgi.frame})
                    frame = res_rm.obj['lab_frame']
                else:
                    frame = pgi.frame
                self.add_reserver_qty(frame, pgi.quantity)
        except Exception as ex:
            logging.critical(str(ex))
            rm.capture_execption(ex)

        return rm

    def subtract_reserver_qty(self, sku, quantity):
        rm = response_message()
        try:
            ois = inventory_struct.objects.get(sku=sku)
            qty = ois.reserve_quantity - quantity
            print(qty)
            if qty < 0:
                rm.code = '-1'
                rm.message = '预定数量错误'
                return rm

            ois.reserve_quantity = qty
            ois.save()
        except Exception as ex:
            logging.critical(str(ex))
            rm.capture_execption(ex)

        return rm

    def sync_web_data(self, sku):
        rm = response_message()
        try:
            wi = web_inventory()
            data = wi.sync_web_data(sku)
            if type(data).__name__ == 'list':
                if len(data) == 0:
                    return rm.response_dict(code='-1', msg='操作失败')

                for item in data:
                    iiss = inventory_struct.objects.filter(sku=item['sku'])
                    if len(iiss) > 0:
                        iis = iiss[0]
                        qty = iis.quantity - iis.reserve_quantity - int(item['quantity_on_stock']) - iis.lock_quantity - iis.no_sale_quantity
                        iis.web_quantity = item['quantity_on_stock']
                        iis.status = item['lab_status']
                        iis.web_status = item['status']
                        iis.oms_web_diff = qty
                        iis.save()
            else:
                if data['code'] == 0:
                    item = data['objects'][sku]['options']
                    iis = inventory_struct.objects.get(sku=sku)
                    qty = iis.quantity - iis.reserve_quantity - int(item['quantity_on_stock']) - iis.lock_quantity - iis.no_sale_quantity
                    iis.web_quantity = item['quantity_on_stock']
                    iis.status = item['lab_status']
                    iis.web_status = item['status']
                    iis.oms_web_diff = qty
                    iis.save()
                else:
                    return rm.response_dict(code='-1', msg='操作失败')
            return rm.response_dict(code='0', msg='success')
        except Exception as ex:
            return rm.response_dict(code='-1', msg=str(ex))

    def sync_reserve_quantity(self, sku):
        rm = response_message()
        try:
            if sku != '':
                sql = """SELECT i.frame AS frame, 
                                i.quantity AS quantity 
                         FROM oms_pgorderitem AS i 
                           LEFT JOIN oms_pgorder AS p 
                           ON  i.pg_order_entity_id = p.id 
                         WHERE p.is_inlab=FALSE 
                           AND p.status <> 'closed'
                           AND p.status <> 'canceled'
                           AND i.frame LIKE '%%%s%%'
                """ % sku

                with connections['pg_oms_query'].cursor() as cursor:
                    iis = inventory_struct.objects.get(sku=sku)
                    iis.reserve_quantity = 1
                    iis.save()
                    cursor.execute(sql)
                    items = namedtuplefetchall(cursor)
                    qty = 0
                    for item in items:
                        qty = qty + int(item.quantity)
                    lab_sql = """SELECT frame, quantity FROM oms_laborder  WHERE frame="%s" AND (`status` in ('', NULL, 'REQUEST_NOTES') OR (`status`='ONHOLD' AND current_status in ('', NULL, 'REQUEST_NOTES')))""" % sku

                    cursor.execute(lab_sql)
                    laborders = namedtuplefetchall(cursor)
                    for item in laborders:
                        qty = qty + int(item.quantity)
                    iis.reserve_quantity = qty
                    iis.save()
            else:
                inventory_struct.objects.all().update(reserve_quantity=0)
                sql = """SELECT i.frame as frame, 
                              SUM(i.quantity) AS quantity 
                       FROM oms_pgorder AS p 
                         LEFT JOIN oms_pgorderitem AS i 
                         ON p.id = i.pg_order_entity_id 
                       WHERE p.is_inlab=FALSE                     
                            AND p.status <> 'closed'
                            AND p.status <> 'canceled' GROUP BY i.frame
                """
                poc = pgorder_frame_controller()
                with connections['pg_oms_query'].cursor() as cursor:
                    cursor.execute(sql)
                    items = namedtuplefetchall(cursor)
                    for item in items:
                        try:
                            #frame = item.frame[1:8]
                            res_rm = poc.get_lab_frame({"pg_frame": item.frame})
                            frame = res_rm.obj['lab_frame']
                            iis = inventory_struct.objects.get(sku=frame)
                            qty = iis.reserve_quantity + item.quantity
                            iis.reserve_quantity = qty
                            iis.save()
                        except Exception as e:
                            pass

                    lab_sql = """SELECT frame, SUM(quantity) AS quantity FROM oms_laborder  WHERE (`status` in ('', NULL, 'REQUEST_NOTES') OR (`status`='ONHOLD' AND current_status in ('', NULL, 'REQUEST_NOTES'))) GROUP BY frame"""
                    cursor.execute(lab_sql)
                    laborders = namedtuplefetchall(cursor)
                    for item in laborders:
                        try:
                            iis = inventory_struct.objects.get(sku=item.frame)
                            qty = iis.reserve_quantity + item.quantity
                            iis.reserve_quantity = qty
                            iis.save()
                        except Exception as e:
                            pass

            return rm.response_dict(code='0', msg='操作成功')
        except Exception as ex:
            return rm.response_dict(code='-1', msg='操作失败')
    # 库存结构表 - 动态生成


class inventory_struct_warehouse(inventory_struct_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='ISTW', editable=False)
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    warehouse_code = models.CharField(u'Code', max_length=40)
    warehouse_name = models.CharField(u'Name', max_length=256)

    @property
    def get_status(self):
        try:
            ins = inventory_struct.objects.get(sku=self.sku)
            return ins.status
        except Exception as e:
            return ''


class inventory_struct_warehouse_controller:

    def get_location(self, sku, warehouse):
        try:
            isw = inventory_struct_warehouse.objects.get(sku=sku, warehouse_code=warehouse)
            logging.debug("SKU:%s Location:%s" % (sku, isw.location))
            return isw.location
        except Exception as ex:
            logging.error('get location ex:%s' % str(ex))
            return None


# 库存初始化
class inventory_initial(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OIST', editable=False)

    sku = models.CharField(u'SKU', max_length=40, default='', unique=True, null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)


# 库存出库单
class inventory_delivery(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OIND', editable=False)

    DOC_TYPE_CHOICES = (
        # ('AUTO', '系统自动'),
        # ('GENERAL_IN', '一般类型入库'),
        # ('REFUNDS_IN', '订单退货入库'),
        ('FAULTY', '报损出库'),
        ('GENERAL_OUT', '一般类型出库'),
        ('STOCK_TAKING', '库存盘点差异调整'),
        ('ALLOTTED_OUT', '调拨出库'),
        ('SAMPLE_OUT', '样品出库'),
        ('REFUNDS_OUT', '订单退货出库'),
    )

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)  # 自动出库 ，和报损出库必填

    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


class inventory_delivery_control:
    def add(self, request, p_number, warehouse_code, sku, doc_type, quantity=1, comments="", lab_number="",
            product_type=1):
        rm = response_message()
        msg = ''
        is_update = True  # 标识是否需要跟新用户信息
        try:
            with transaction.atomic():
                # 验证SKU格式
                #sku = sku.upper()
                # reg = r"^[0-9][0-9][0-9][0-9][A-Z][A-Z0-9][0-9]$"
                # SKU_str = re.match(reg, sku)
                # if SKU_str == None:
                #     rm.code = -1
                #     rm.message = "SKU格式不正确"
                #     return rm

                # 验证/获取要加入的 warehouse
                whs = warehouse.objects.filter(code=warehouse_code)
                if whs.count() == 0:
                    rm.code = -2
                    rm.message = "相关工厂信息不存在"
                    return rm
                else:
                    wh = whs[0]

                # 目前只有一种类型的产品
                prod = None
                if product_type == 1:
                    # 查询镜架产品是否存在
                    product = product_frame.objects.filter(sku=sku)
                    msg = msg + "|" + sku
                    msg = msg + "|" + str(product.count())

                    if product.count() == 0:
                        # 12.27 以仓库数据为主 不判断product_frame是否存在
                        prod = product_frame()
                        prod.sku = sku
                        prod.comments = "由系统自动创建"
                        prod.save()

                    else:
                        prod = product[0]

                else:
                    rm.code = -4
                    rm.message = '该功能尚未启用'
                    return rm

                invsws = inventory_struct_warehouse.objects.filter(sku=sku).filter(warehouse_code=warehouse_code)
                msg = msg + "|" + "struct_warehouse_count|" + str(invsws.count())
                if invsws.count() == 0:
                    if doc_type == "AUTO":
                        invsw = inventory_struct_warehouse()
                    else:
                        rm.code = -3
                        rm.message = '产品不存在 只有【自动出库】可以新建条目'
                        return rm
                else:
                    invsw = invsws[0]

                if doc_type == "AUTO":
                    isc = inventory_struct_contoller()
                    isc.subtract_reserver_qty(sku, quantity)

                invsw.sku = sku
                invsw.warehouse_code = wh.code
                invsw.warehouse_name = wh.name
                invsw.name = prod.name
                invsw.quantity = invsw.quantity - int(quantity)
                invsw.user_id = request.user.id
                invsw.user_name = request.user.username
                invsw.save()

                # 创建 inventory_receipt 实例
                invd = inventory_delivery()

                invd.doc_number = p_number

                invd.warehouse = wh
                invd.warehouse_code = wh.code
                invd.warehouse_name = wh.name

                invd.sku = sku
                invd.quantity = quantity
                invd.name = prod.name
                invd.doc_type = doc_type
                invd.lab_number = lab_number
                # if not lab_number == "":
                #     invd.comments = lab_number
                invd.user_id = request.user.id
                invd.user_name = request.user.username
                invd.comments = comments
                logging.debug('inventory_delivery开始创建')
                invd.save()
                logging.debug('inventory_delivery创建成功')
                # 查询对应的 wms_inventory_struct 和 wms_inventory_struct_warehouse
                # wms_inventory_struct 只是通过 SKU ,出库时减少对应 quantity
                # wms_inventory_struct_warehouse 通过 SKU 和 warehouse 筛选, 出库减少库存量

                struct = inventory_struct.objects.filter(sku=sku)
                msg = msg + "|" + "struct_count|" + str(struct.count())
                if struct.count() == 0:
                    # 12.27 以各仓库数据为主 不判断inventory_struct是否存在
                    invs = inventory_struct()
                else:
                    invs = struct[0]

                invs.sku = prod.sku
                invs.name = prod.name
                invs.quantity = invs.quantity - int(quantity)
                invs.user_id = request.user.id
                invs.user_name = request.user.username
                invs.save()

                # rm.message 用来标识流程进行到哪里
                rm.message = msg

        except Exception as e:
            logging.debug(str(e))
            rm.code = -9
            rm.message = msg + "exception:" + str(e)

        return rm


    def add_new(self, request, data_dict):
        rm = response_message()
        msg = ''
        is_update = True  # 标识是否需要跟新用户信息
        try:
            p_number = data_dict.get('p_number', '')
            warehouse_code = data_dict.get('wh_number', '')
            sku = data_dict.get('sku', '')
            doc_type = data_dict.get('doc_type', '')
            quantity = data_dict.get('quantity', 1)
            comments = data_dict.get('comments', '')
            lab_number = data_dict.get('lab_number_input', '')
            product_type = data_dict.get('product_type', 1)
            wh_channel = data_dict.get('wh_channel', '')
            with transaction.atomic():
                # 验证/获取要加入的 warehouse
                whs = warehouse.objects.filter(code=warehouse_code)
                if whs.count() == 0:
                    rm.code = -2
                    rm.message = "获取仓库出错"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    wh = whs[0]

                # 目前只有一种类型的产品
                prod = None
                if product_type == 1:
                    # 查询镜架产品是否存在
                    product = product_frame.objects.filter(sku=sku)
                    msg = msg + "|" + sku
                    msg = msg + "|" + str(product.count())

                    if product.count() == 0:
                        rm.code = -1
                        rm.message = "product_frame中不存在该sku"
                        raise MyException(rm.code, rm.message)
                    else:
                        prod = product[0]
                else:
                    rm.code = -4
                    rm.message = '该功能尚未启用'
                    raise MyException(rm.code, rm.message)

                # 查询对应的 wms_inventory_struct 和 wms_inventory_struct_warehouse
                # wms_inventory_struct 只是通过 SKU ,出库时减少对应 quantity
                # wms_inventory_struct_warehouse 通过 SKU 和 warehouse 筛选, 出库减少库存量
                invsws = inventory_struct_warehouse.objects.filter(sku=sku).filter(warehouse_code=warehouse_code)
                msg = msg + "|" + "struct_warehouse_count|" + str(invsws.count())
                if invsws.count() == 0:
                    if doc_type == "AUTO":
                        invsw = inventory_struct_warehouse()
                    else:
                        rm.code = -3
                        rm.message = '产品不存在 只有【自动出库】可以新建条目'
                        raise MyException(rm.code, rm.message)
                else:
                    invsw = invsws[0]


                invsw_diff_quantity = invsw.quantity - int(quantity)
                if invsw_diff_quantity < 0:
                    rm.code = -3
                    rm.message = 'struct_warehouse_count 中数量不足'
                    raise MyException(rm.code, rm.message)

                invsw.sku = sku
                invsw.warehouse_code = wh.code
                invsw.warehouse_name = wh.name
                invsw.name = prod.name
                invsw.quantity = invsw_diff_quantity
                invsw.user_id = request.user.id
                invsw.user_name = request.user.username
                invsw.save()
                #自动出库不做处理，出库数量大于库存仓库表中数量不允许出库
                if doc_type == "AUTO":
                    isc = inventory_struct_contoller()
                    isc.subtract_reserver_qty(sku, quantity)
                # else:
                #     diff_qty = invsw.quantity - int(quantity)
                #     if diff_qty < 0:
                #         rm.code = -3
                #         rm.message = '库存仓库表中数量小于出库数量'
                #         raise MyException(rm.code, rm.message)

                struct = inventory_struct.objects.filter(sku=sku)
                msg = msg + "|" + "struct_count|" + str(struct.count())
                if struct.count() == 0:
                    # 12.27 以各仓库数据为主 不判断inventory_struct是否存在
                    invs = inventory_struct()
                else:
                    invs = struct[0]

                invs_diff_quantity = invs.quantity - int(quantity)

                if invs_diff_quantity < 0:
                    rm.code = -3
                    rm.message = 'inventory_struct 中数量不足'
                    raise MyException(rm.code, rm.message)

                if not wh.is_sale:
                    diff_no_sale_qty = invs.no_sale_quantity - int(quantity)
                    if diff_no_sale_qty < 0:
                        diff_no_sale_qty = 0
                    invs.no_sale_quantity = diff_no_sale_qty

                invs.sku = prod.sku
                invs.name = prod.name
                invs.quantity = invs_diff_quantity
                invs.user_id = request.user.id
                invs.user_name = request.user.username
                invs.save()

                # 创建出库inventory_delivery记录
                invd = inventory_delivery()
                invd.doc_number = p_number
                invd.warehouse = wh
                invd.warehouse_code = wh.code
                invd.warehouse_name = wh.name
                invd.sku = sku
                invd.quantity = quantity
                invd.name = prod.name
                invd.doc_type = doc_type
                invd.lab_number = lab_number
                invd.user_id = request.user.id
                invd.user_name = request.user.username
                invd.comments = comments
                logging.debug('inventory_delivery开始创建')
                invd.save()
                logging.debug('inventory_delivery创建成功')

            if wh.is_sale:
                # 报损出库 库存盘点差异调整 样品出库 一般类型出库 时调用inventory_delivery_channel_controller()
                if doc_type == 'FAULTY' or doc_type == 'STOCK_TAKING' or doc_type == 'SAMPLE_OUT' or doc_type == 'GENERAL_OUT':
                    idcc = inventory_delivery_channel_controller()

                    al_quantity = invs.al_quantity
                    diff_al_del_quantity = al_quantity - int(quantity)
                    if diff_al_del_quantity >= 0:
                        invs.al_quantity = diff_al_del_quantity
                        invs.save()
                    elif diff_al_del_quantity < 0 and al_quantity > 0:
                        invs.al_quantity = 0
                        invs.save()
                        qty = abs(diff_al_del_quantity)
                        res = idcc.add(request, p_number, wh_channel, doc_type, sku, int(qty))

                        if not res.code == 0:
                            rm.code = -3
                            rm.message = '接口错误：{0}'.format(res.message)
                            raise MyException(rm.code, rm.message)
                    elif diff_al_del_quantity < 0 and al_quantity == 0:
                        res = idcc.add(request, p_number, wh_channel, doc_type, sku, int(quantity))

                        if not res.code == 0:
                            rm.code = -3
                            rm.message = '接口错误：{0}'.format(res.message)
                            raise MyException(rm.code, rm.message)

                # rm.message 用来标识流程进行到哪里
            rm.message = msg

        except Exception as e:
            logging.debug(str(e))
            rm.code = e.code
            rm.message = e.message

        return rm


    def check_quantity(self, sku, quantity):
        # 库存数量
        try:
            rm = response_message()
            ois = inventory_struct_warehouse.objects.get(sku=sku, warehouse_code=warehouse_code)
            diff_quantity = int(ois.quantity) - int(quantity)
            if diff_quantity < 0 or int(ois.quantity) < 0:
                rm.code = -1
                rm.message = u'库存数量小于出库数量,请人工确认'
                return rm
        except Exception as e:
            logging.debug(str(e))
            rm.code = -9
            rm.message = "exception:" + str(e)
        return rm

    @staticmethod
    def get_doctype_choices():
        doctype_dict = {}
        delr_choices = inventory_delivery.DOC_TYPE_CHOICES
        for t_key in delr_choices:
            doctype_dict[t_key[0]] = t_key[1]

        return doctype_dict


# 库存入库单
class inventory_receipt(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OINR', editable=False)

    DOC_TYPE_CHOICES = (
        # ('GENERAL_OUT', '一般类型出库'),
        #('GENERAL_IN', '一般类型入库'),
        ('REFUNDS_IN', '订单退货入库'),
        # ('FAULTY', '报损出库'),
        ('STOCK_TAKING', '库存盘点差异调整'),
        # ('ALLOTTED_IN', '调拨入库'),
        ('SAMPLE_IN', '样品入库'),
        # ('AUTO', '系统自动'),
        ('NP_IN', '新品入库'),
        ('RP_IN', '补货入库'),
    )

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)  # 订单退货入库填写

    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


class inventory_receipt_control:
    def add(self, request, p_number, warehouse_code, sku, price, doc_type, quantity=1, comments="",
            lab_number='',
            product_type=1):
        rm = response_message()
        msg = ''
        try:
            with transaction.atomic():
                # 验证SKU格式
                # reg = r"^[0-9][0-9][0-9][0-9][A-Z][A-Z0-9][0-9]$"
                # SKU_str = re.match(reg, sku)
                # if SKU_str == None:
                #     rm.code = -3
                #     rm.message = "SKU格式不正确"
                #     return rm

                # 验证/获取要加入的 warehouse
                whs = warehouse.objects.filter(code=warehouse_code)
                if whs.count() == 0:
                    rm.code = -2
                    rm.message = "获取仓库出错"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    wh = whs[0]

                # 产品
                prod = None
                if product_type == 1:
                    # 填充 inventory_receipt 通过 product_frame 的 name 和 warehouse 的 code
                    product_count = product_frame.objects.filter(sku=sku).count()
                    msg = msg + "|" + sku
                    msg = msg + "|" + str(product_count)
                    if product_count == 0:
                        # prod = product_frame()
                        # prod.sku = sku
                        # prod.comments = "由系统自动创建"
                        # prod.save()
                        if doc_type != 'NP_IN':
                            rm.code = -1
                            rm.message = 'product_frame中不存在该SKU'
                            raise MyException(rm.code, rm.message)
                        else:
                            rm.code = -1
                            rm.message = '请到SKU新建&维护功能创建该SKU'
                            raise MyException(rm.code, rm.message)
                            # prod = product_frame()
                            # prod.sku = sku
                            # prod.comments = "由系统自动创建"
                            # prod.save()
                    else:
                        prod = product_frame.objects.get(sku=sku)

                else:
                    rm.code = -2
                    rm.message = '该功能尚未启用'
                    raise MyException(rm.code, rm.message)


                # 填充对应的 wms_inventory_struct 和 wms_inventory_struct_warehouse
                # wms_inventory_struct 只是通过 SKU ,入库时增加对应 quantity
                # wms_inventory_struct_warehouse 通过 SKU 和 warehouse 筛选, 入库增加库存量

                struct_count = inventory_struct.objects.filter(sku=sku).count()
                msg = msg + "|" + "struct_count|" + str(struct_count)
                if struct_count == 0:
                    invs = inventory_struct()
                else:
                    invs = inventory_struct.objects.get(sku=sku)

                invs.sku = prod.sku
                invs.name = prod.name
                invs.quantity = invs.quantity + int(quantity)
                if wh.is_sale:
                    if doc_type != 'ALLOTTED_IN':
                        invs.al_quantity = invs.al_quantity + int(quantity)

                if not wh.is_sale:
                    invs.no_sale_quantity = invs.no_sale_quantity + int(quantity)

                invs.user_id = request.user.id
                invs.user_name = request.user.username
                invs.save()

                invsws = inventory_struct_warehouse.objects.filter(sku=sku).filter(warehouse_code=warehouse_code)
                msg = msg + "|" + "struct_warehouse_count|" + str(invsws.count())
                if invsws.count() == 0:
                    invsw = inventory_struct_warehouse()
                else:
                    invsw = invsws[0]

                invsw.sku = sku
                invsw.warehouse_code = wh.code
                invsw.warehouse_name = wh.name
                invsw.name = prod.name
                invsw.quantity = invsw.quantity + int(quantity)
                invsw.save()

                # 创建 inventory_receipt 实例
                invr = inventory_receipt()
                invr.doc_number = p_number
                invr.warehouse = wh
                invr.warehouse_code = wh.code
                invr.warehouse_name = wh.name
                invr.sku = sku
                invr.quantity = quantity
                invr.price = price
                invr.name = prod.name
                invr.doc_type = doc_type
                invr.lab_number = lab_number

                invr.user_id = request.user.id
                invr.user_name = request.user.username
                invr.comments = comments
                invr.save()

                # rm.message 用来标识流程进行到哪里
                rm.message = msg

        except Exception as e:
            logging.debug(str(e))
            rm.code = -1
            rm.message = e.message

        return rm

    @staticmethod
    def get_doctype_choices():
        doctype_dict = {}
        invr_choices = inventory_receipt.DOC_TYPE_CHOICES
        for t_key in invr_choices:
            doctype_dict[t_key[0]] = t_key[1]

        return doctype_dict


# 库存盘点表
class stock_taking(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OSTO', editable=False)

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity_origin = models.DecimalField(u'Origin Quantity', max_digits=10, decimal_places=0, default=0)
    quantity_target = models.DecimalField(u'Target Quantity', max_digits=10, decimal_places=0, default=0)


# 镜片
# 用于 工厂 SKU 的进一步细化
class lens_extend(product_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='LENE', editable=False)

    index = models.CharField(u'Lens Index', max_length=20, default='1.56',
                             choices=LENS_INDEX_CHOICES)

    quantity = models.IntegerField(u'Quantity', default=-1)

    lens_type = models.CharField(u'Lens type', max_length=20, default='0',
                                 choices=LENS_TYPE_CHOICES)

    material = models.CharField(u'Material', max_length=128, default='', null=True, blank=True)
    brand = models.CharField(u'Brand', max_length=128, default='', null=True, blank=True)
    series = models.CharField(u'Series', max_length=128, default='', null=True, blank=True)
    base_sku = models.CharField(u'Base SKU', max_length=128, default='', null=True)

    bar_code = models.CharField(u'Bar Code', max_length=128, default='', null=True, blank=True)


# 镜片库存表-基类
class inventory_struct_lens_base(base_type):
    class Meta:
        abstract = True

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    base_sku = models.CharField(u'BASE SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    entity_id = models.CharField(u'Entity ID', max_length=20, default='', unique=True, null=True)
    reference_code = models.CharField(u'Reference Code', max_length=128, default='', null=True, blank=True)
    luminosity_type = models.CharField(u'Luminosity Type', max_length=20, default='', null=True, blank=True)
    sph = models.DecimalField(u'SPH', max_digits=5, decimal_places=2, default=0)
    cyl = models.DecimalField(u'CYL', max_digits=5, decimal_places=2, default=0)
    add = models.DecimalField(u'ADD', max_digits=5, decimal_places=2, default=0)
    diameter = models.IntegerField(u'Diameter', default=0)
    coating = models.CharField(u'Coating', max_length=20, default='')
    coating_color = models.CharField(u'Coating_color', max_length=20, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0, null=True, blank=True)

    location = models.CharField(u'Location', max_length=128, default='', null=True, blank=True)
    batch_number = models.CharField(u'Batch Number', max_length=20, default='201900', null=True)


# 镜片库存表—库存初始化
class inventory_initial_lens(inventory_struct_lens_base):
    type = models.CharField(u'Type', max_length=20, default='OIIL', editable=False)
    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


class inventory_initial_lens_controller():
    def add(self, warehouse_code, sku, sph, cyl, add, quantity, entity_id='', comments=''):
        # base---squence,is_enabled,created_at,updated_at
        # lens---user_id,user_name,base_sku,name,diameter,coating,
        # null---entity_id,reference_code,luminosity,location,batch_number
        rm = response_message()
        try:
            # 获取prodect_lens对象
            try:
                pl = product_lens.objects.get(sku=str(sku))
            except Exception as e:
                logging.critical("错误：" + str(e))
                rm.capture_execption(e)
                rm.message = '未获取到SKU：' + sku + '的product_lens数据'
                return rm
            # 数据类型转换
            try:
                cyl = float(cyl)
                sph = float(sph)
                add = float(add)
                quantity = int(quantity)
            except Exception as e:
                logging.debug('错误：' + str(e))
                rm.capture_execption(e)
                msg = '数据类型转换出错'
                rm.message = msg
                return rm

            iil = inventory_initial_lens()
            iil.user_id = 0
            iil.user_name = "System"
            iil.comments = comments
            iil.warehouse_code = warehouse_code
            iil.sku = sku
            iil.base_sku = pl.base_sku
            iil.name = pl.name
            # iil.entity_id 默认空
            # iil.reference_code 默认空
            if sph <= 0:
                iil.luminosity_type = 'N'
            else:
                iil.luminosity_type = 'P'
            iil.sph = sph
            iil.cyl = cyl
            iil.add = add
            iil.diameter = pl.diameter
            iil.coating = pl.coating
            iil.coating_color = pl.coating_color
            iil.quantity = quantity
            # iil.location
            # iil.batch_number入库时生成
            iil.save()

            # entityid为空则生成 entity_id  条形码编号
            if entity_id == '':
                str_id = str(iil.id).zfill(7)
                iil.entity_id = '1' + str_id  # 7位前补0
            else:
                iil.entity_id = entity_id
            iil.save()
            rm.message += ',id=' + str(iil.id)
        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
            return rm
        return rm


class inventory_struct_lens_controller:
    '''
    2019.10.27 by guof.
    增加基于 base_sku/sph/cyl 查询当前镜片库存量
    '''
    def get_qty(self, params):
        rm = response_message()

        try:
            base_sku = params.get("base_sku", "")
            sph = params.get("sph", "")
            cyl = params.get("cyl", "")
            isls = inventory_struct_lens.objects.filter(base_sku=base_sku, sph=sph, cyl=cyl)
            if len(isls) == 0:
                rm.count = 0
            else:
                isl = isls[0]
                rm.count = isl.quantity

        except Exception as ex:
            rm.capture_execption(ex)

        return rm

# 镜片库存表—基础数据
class product_lens(product_base):
    PRODUCT_TYPE_CHOICES = product_base.PRODUCT_TYPE_CHOICES
    product_type = models.CharField(u'PRODUCT TYPE', max_length=15, default='LENS',
                                    choices=PRODUCT_TYPE_CHOICES)

    base_sku = models.CharField(u'Base SKU', max_length=128, default='', null=True)
    index = models.CharField(u'Lens Index', max_length=20, default='1.56',
                             choices=LENS_INDEX_CHOICES)

    lens_type = models.CharField(u'Lens type', max_length=20, default='0',
                                 choices=LENS_TYPE_CHOICES)

    quantity = models.IntegerField(u'Quantity', default=-1)

    material = models.CharField(u'Material', max_length=128, default='', null=True, blank=True)
    brand = models.CharField(u'Brand', max_length=128, default='', null=True, blank=True)
    series = models.CharField(u'Series', max_length=128, default='', null=True, blank=True)
    diameter = models.IntegerField(u'直径', default=0, null=True, blank=True)
    coating = models.CharField(u'Coating', max_length=20, default='', null=True, blank=True)
    coating_color = models.CharField(u'Coating_color', max_length=20, default='', null=True, blank=True)
    grade = models.CharField(u'Grade', max_length=10, default='', null=True, blank=True)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    luminosity_type = models.CharField(u'Luminosity Type', max_length=20, default='', null=True, blank=True)

    vendor_code = models.CharField(u'VD', max_length=20, null=True, blank=True, default='0')
    vendor_name = models.CharField(u'VD_NAME', max_length=128, null=True, blank=True, default='0')


# 镜片库存表-基础库存
class inventory_struct_lens(inventory_struct_lens_base):
    type = models.CharField(u'Type', max_length=20, default='OISI', editable=False)


# 镜片库存表-基础库存-批次
class inventory_struct_lens_batch(inventory_struct_lens_base):
    type = models.CharField(u'Type', max_length=20, default='ISLB', editable=False)
    entity_id = models.CharField(u'Entity ID', max_length=20, default='', unique=False, null=True, blank=True)  # 重写
    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


# 镜片库存表-出库
class inventory_delivery_lens(documents_base):
    type = models.CharField(u'Type', max_length=20, default='INDL', editable=False)

    DOC_TYPE_CHOICES = (
        # ('AUTO', '系统自动'),
        # ('GENERAL_IN', '一般类型入库'),
        # ('REFUNDS_IN', '订单退货入库'),
        ('FAULTY', '报损出库'),
        ('GENERAL_OUT', '一般类型出库'),
        ('STOCK_TAKING', '库存盘点差异调整'),
        ('ALLOTTED_OUT', '调拨出库'),
        ('SAMPLE_OUT', '样品出库'),
        ('REFUNDS_OUT', '订单退货出库'),
    )
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    luminosity_type = models.CharField(u'Luminosity Type', max_length=20, default='')
    sph = models.DecimalField(u'SPH', max_digits=5, decimal_places=2, default=0)
    cyl = models.DecimalField(u'CYL', max_digits=5, decimal_places=2, default=0)
    add = models.DecimalField(u'ADD', max_digits=5, decimal_places=2, default=0)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    base_sku = models.CharField(u'Base SKU', max_length=40, default='', null=True)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)  # 自动出库 ，和报损出库必填

    # warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


# 镜片出库controller
class inventory_delivery_lens_controller():
    def add(self, request, doc_number, doc_type, warehouse_code, sku, sph, cyl, add, quantity=1, batch_number='',
            comments='', lab_number=''):
        rm = response_message()
        msg = ''
        try:
            user_id = 0
            user_name = 'System'
            if request:
                user_id = request.user.id
                user_name = request.user.username
            with transaction.atomic():
                logging.debug('*****开始写入镜片出库表******')
                # 数据类型转换
                cyl = float(cyl)
                sph = float(sph)
                add = float(add)
                quantity = int(quantity)

                # 验证/获取要加入的 warehouse
                whs = warehouse.objects.filter(code=warehouse_code)
                if whs.count() == 0:
                    rm.code = -2
                    rm.message = "获取仓库出错"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    wh = whs[0]

                # 查询镜片产品是否存在
                product = product_lens.objects.filter(sku=sku)
                msg = msg + "|" + sku
                msg = msg + "|" + str(product.count())
                if product.count() == 0:
                    rm.code = -2
                    rm.message = "相关SKU信息不存在"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    pl = product[0]
                    logging.debug('找到SKU')
                # 更新，镜片库存表的数量
                isls = inventory_struct_lens.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add)
                isls_count = isls.count()
                if isls_count > 0:
                    # 保存库存表
                    isl = isls[0]
                    diff_quantity = isl.quantity - quantity
                    if diff_quantity < 0:
                        rm.code = -2
                        rm.message = "库存总表，数量不足"
                        raise MyException(rm.code, rm.message)
                    isl.quantity = diff_quantity
                    isl.save()
                    logging.debug('镜片库存表，更新成功')
                else:
                    logging.debug('出库单保存失败')
                    logging.debug('sku:' + str(sku) + ' sph:' + str(sph) + '  cyl:' + str(cyl) + '  add:' + str(add))
                    rm.code = -2
                    rm.message = "库存表，信息不存在"
                    raise MyException(rm.code, rm.message)

                # 判断批号是否给出
                if batch_number == '':
                    isls = inventory_struct_lens_batch.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add,
                                                                      warehouse_code=warehouse_code).order_by(
                        'batch_number')
                else:
                    isls = inventory_struct_lens_batch.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add,
                                                                      warehouse_code=warehouse_code,
                                                                      batch_number=batch_number)
                isls_count = isls.count()
                if isls_count == 0:
                    rm.code = -2
                    rm.message = "库存—批次表，信息不存在"
                    raise MyException(rm.code, rm.message)
                else:
                    # 遍历库存列表，遇到不为0的批次减少
                    delivery_index = 0  # 出库成功标志
                    for isl in isls:
                        if isl.quantity > 0:
                            if isl.quantity - quantity < 0:  # 当前批次不够减
                                quantity -= isl.quantity
                                isl.quantity = 0
                                isl.save()
                            else:  # 当前批次够减
                                isl.quantity -= quantity
                                isl.save()
                                logging.debug('镜片库存—批号表，更新成功')
                                delivery_index = 1
                                break
                    # 出库成功标志为 0
                    if delivery_index == 0:
                        rm.code = -2
                        rm.message = "批号表库存数量不足"
                        raise MyException(rm.code, rm.message)

                # 创建 inventory_delivery_lens 实例
                idl = inventory_delivery_lens()
                idl.user_id = user_id
                idl.user_name = user_name
                idl.comments = comments

                idl.doc_type = doc_type
                idl.doc_number = doc_number
                # irl.status = status
                # idl.base_entity = base_entity

                idl.sku = sku
                idl.base_sku = pl.base_sku
                idl.name = pl.name
                # 光度参数
                if float(sph) <= 0:
                    idl.luminosity_type = 'N'
                else:
                    idl.luminosity_type = 'P'
                idl.sph = sph
                idl.cyl = cyl
                idl.add = add

                idl.quantity = quantity
                idl.warehouse = wh
                idl.warehouse_code = wh.code
                idl.warehouse_name = wh.name
                idl.lab_number = lab_number
                idl.save()
        except Exception as e:
            logging.debug('错误：' + str(e))
            rm.capture_execption(e)
            rm.message = e.message

        return rm

    @staticmethod
    def get_doctype_choices():
        doctype_dict = {}
        delr_choices = inventory_delivery_lens.DOC_TYPE_CHOICES
        for t_key in delr_choices:
            doctype_dict[t_key[0]] = t_key[1]

        return doctype_dict


# 镜片库存表-入库
class inventory_receipt_lens(documents_base):
    type = models.CharField(u'Type', max_length=20, default='INRL', editable=False)

    DOC_TYPE_CHOICES = (
        # ('GENERAL_OUT', '一般类型出库'),
        ('GENERAL_IN', '一般类型入库'),
        ('REFUNDS_IN', '订单退货入库'),
        # ('FAULTY', '报损出库'),
        ('STOCK_TAKING', '库存盘点差异调整'),
        ('ALLOTTED_IN', '调拨入库'),
        ('SAMPLE_IN', '样品入库'),
        # ('INIT','库存初始化'),
        # ('AUTO', '系统自动'),
    )

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    # lens_entity_id = models.CharField(u'Entity ID', max_length=20, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    luminosity_type = models.CharField(u'Luminosity Type', max_length=20, default='')
    sph = models.DecimalField(u'SPH', max_digits=5, decimal_places=2, default=0)
    cyl = models.DecimalField(u'CYL', max_digits=5, decimal_places=2, default=0)
    add = models.DecimalField(u'ADD', max_digits=5, decimal_places=2, default=0)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)
    base_sku = models.CharField(u'Base SKU', max_length=40, default='', null=True)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)  # 订单退货入库填写

    # warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_code = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=256, default='', null=True)


# 镜片入库controller
class inventory_receipt_lens_controller():
    def add(self, request, doc_number, doc_type, warehouse_code, sku, quantity, sph, cyl, add, price=0, location='',
            entity_id='', batch_number='', comments='', lab_number=''):
        logging.debug('*****开始写入入库表******')
        rm = response_message()
        msg = ''
        try:
            with transaction.atomic():
                # 数据类型转换
                cyl = float(cyl)
                sph = float(sph)
                add = float(add)
                quantity = int(quantity)
                # 验证/获取要加入的 warehouse
                whs = warehouse.objects.filter(code=warehouse_code)
                if whs.count() == 0:
                    rm.code = -2
                    rm.message = "获取仓库出错"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    wh = whs[0]

                if float(sph) <= 0:
                    luminosity_type = 'N'
                else:
                    luminosity_type = 'P'

                # 根据SKU找到product_lens
                pls = product_lens.objects.filter(sku=sku)
                if pls.count() == 0:
                    rm.code = -2
                    rm.message = "获取peoduct_lens出错"
                    logging.debug(rm.message)
                    raise MyException(rm.code, rm.message)
                else:
                    pl = pls[0]

                # 判断数据的光度类型和product_lens光度类型是否一致
                if not pl.luminosity_type == luminosity_type:
                    rm.code = -2
                    msg = '光度类型不匹配'
                    rm.message = msg
                    raise MyException(rm.code, rm.message)

                # cyl不能为正
                if cyl > 0:
                    rm.code = -2
                    msg = '暂不支持正cyl'
                    rm.message = msg
                    raise MyException(rm.code, rm.message)

                # 判断request是否为空
                if request:
                    user_id = request.user.id
                    user_name = request.user.username
                else:
                    user_id = 0
                    user_name = 'System'

                # 判断price是否为空
                if price == 0:
                    price = pl.price

                # 填充对应的 inventory_struct_lens 不管批次 batch_number
                # 查找是否已存在记录
                isls = inventory_struct_lens.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add)
                isls_count = isls.count()
                msg = msg + "|" + "struct_count|" + str(isls_count)
                logging.debug('msg:%s' % msg)
                if isls_count == 0:
                    # 写入新纪录
                    isl = inventory_struct_lens()
                    isl.user_id = user_id
                    isl.user_name = user_name

                    isl.sku = sku
                    isl.base_sku = pl.base_sku
                    isl.name = pl.name
                    # isl.entity_id = 基于ID拼接，第二次SAVE 补全
                    # isl.reference_code = 预留字段，默认空
                    if float(sph) <= 0:
                        isl.luminosity_type = 'N'
                    else:
                        isl.luminosity_type = 'P'
                    isl.sph = sph
                    isl.cyl = cyl
                    isl.add = add
                    isl.diameter = pl.diameter
                    isl.coating = pl.coating
                    isl.coating_color = pl.coating_color
                    isl.quantity = quantity
                    # isl.batch_number = 默认1900
                    isl.location = location
                    isl.save()
                    # entityid为空则生成 entity_id  条形码编号
                    if entity_id:
                        isl.entity_id = entity_id
                    else:
                        str_id = str(isl.id).zfill(7)
                        isl.entity_id = '1' + str_id  # 7位前补0
                    isl.save()
                else:
                    # 增加原有记录数量
                    isl = isls[0]
                    isl.quantity += quantity
                    isl.save()

                # 生成批号
                if batch_number == '':
                    # 用户未给出批次就基于时间自动生成
                    batch_number = time.strftime('%Y%m', time.localtime(time.time()))

                # 2019.11.23 by guof.
                # 暂时停掉批次管理
                batch_number = '201900'

                # 填充对应的 inventory_struct_lens-batch 对应，仓库及批次
                islbs = inventory_struct_lens_batch.objects.filter(sku=sku, sph=sph, cyl=cyl, add=add,
                                                                   warehouse_code=warehouse_code,
                                                                   batch_number=batch_number)
                islbs_count = islbs.count()
                msg = msg + "|" + "struct_warehouse_count|" + str(islbs_count)
                logging.debug('msg:%s' % msg)
                if islbs_count == 0:
                    # 没有记录则创建
                    islb = inventory_struct_lens_batch()
                    islb.user_id = user_id
                    islb.user_name = user_name

                    islb.sku = sku
                    islb.base_sku = pl.base_sku
                    islb.name = pl.name
                    # islb.entity_id = 基于ID拼接
                    # islb.reference_code = 默认空
                    if float(sph) <= 0:
                        islb.luminosity_type = 'N'
                    else:
                        islb.luminosity_type = 'P'
                    islb.sph = sph
                    islb.cyl = cyl
                    islb.add = add
                    islb.diameter = pl.diameter
                    islb.coating = pl.coating
                    islb.coating_color = pl.coating_color
                    islb.quantity = quantity
                    islb.batch_number = batch_number
                    islb.location = location
                    islb.warehouse_code = warehouse_code
                    islb.warehouse_name = wh.name
                    islb.save()
                    if entity_id:
                        islb.entity_id = entity_id
                    else:
                        # 生成entity_id  条形码编号
                        str_id = str(isl.id).zfill(7)
                        islb.entity_id = '1' + str_id  # 7位前补0

                    islb.save()
                else:
                    # 有记录增加数量
                    islb = islbs[0]
                    islb.quantity += quantity
                    islb.save()

                # 写入入库单
                irl = inventory_receipt_lens()
                irl.user_id = user_id
                irl.user_name = user_name
                irl.comments = comments

                irl.doc_type = doc_type
                irl.doc_number = doc_number
                # irl.status = status
                # irl.base_entity = base_entity

                irl.sku = sku
                irl.base_sku = pl.base_sku
                irl.name = pl.name
                # 光度参数
                if float(sph) <= 0:
                    irl.luminosity_type = 'N'
                else:
                    irl.luminosity_type = 'P'
                irl.sph = sph
                irl.cyl = cyl
                irl.add = add
                irl.quantity = quantity
                irl.price = price
                irl.lab_number = lab_number

                irl.warehouse = wh
                irl.warehouse_code = wh.code
                irl.warehouse_name = wh.name
                irl.save()

                logging.debug('入库单保存成功')

        except Exception as e:
            logging.debug('错误：' + str(e))
            rm.capture_execption(e)
            rm.message = e.message

        return rm

    @staticmethod
    def get_doctype_choices():
        doctype_dict = {}
        invr_choices = inventory_receipt_lens.DOC_TYPE_CHOICES
        for t_key in invr_choices:
            doctype_dict[t_key[0]] = t_key[1]

        return doctype_dict


# 库存操作log表
class inventory_operation_log(base_type):
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    reason = models.CharField(u'原因', max_length=512, default='', blank=True, null=True)
    operation_type = models.CharField(u'操作类型', max_length=128, default='', blank=True)

    def log(self, sku, reason, operation_type, user):
        self.sku = sku
        self.user_name = user.username
        self.user_id = user.id
        self.reason = reason
        self.operation_type = operation_type
        self.save()

    def api_log(self, sku, reason, operation_type,user_id=0, user_name='api'):
        self.sku = sku
        self.user_name = user_name
        self.user_id = user_id
        self.reason = reason
        self.operation_type = operation_type
        self.save()


class channel(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OCHA', editable=False)
    code = models.CharField(u'Code', max_length=40)
    name = models.CharField(u'Name', max_length=256)
    location = models.CharField(u'Location', max_length=512)

    def __str__(self):
        return self.name


# 库存结构渠道表
class inventory_struct_channel(inventory_struct_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OISC', editable=False)
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('IN_STOCK', 'In Stock'),
        ('OUT_OF_STOCK', 'Out of stock'),
    )
    status = models.CharField(u'Status', max_length=40, default='DRAFT',
                              choices=STATUS_CHOICES)
    channel_code = models.CharField(u'CODE', max_length=128, default='', blank=True)
    channel_name = models.CharField(u'NAME', max_length=128, default='', blank=True)


# 库存渠道入库单
class inventory_receipt_channel(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    STATUS_CHOICES = (
        ('0', '执行成功'),
        ('1', '执行失败'),
        ('2', '未执行')
    )
    type = models.CharField(u'Type', max_length=20, default='OIRC', editable=False)
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    channel_code = models.CharField(u'CODE', max_length=128, default='', blank=True)
    channel_name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)
    success_status = models.CharField(u'Status', max_length=40, default='2',
                                      choices=STATUS_CHOICES)
    message = models.CharField(u'message', max_length=512, default='', blank=True, null=True)


class inventory_receipt_channel_controller():
    def add(self, request, p_number, channel_code, doc_type, sku, quantity, comments=''):
        rm = response_message()
        try:
            #with transaction.atomic():
            if request is not None:
                user_id = request.user.id
                user_name = request.user.username
            else:
                user_id = 0
                user_name = 'system'

            try:
                try:
                    pf = product_frame.objects.get(sku=sku)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到SKU：' + sku + '的product_frame数据'
                    return rm

                try:
                    ois = inventory_struct.objects.get(sku=sku)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到SKU：' + sku + '的inventory_struct数据'
                    return rm

                try:
                    ch = channel.objects.get(code=channel_code)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到code：' + channel_code + '的channel数据'
                    return rm

                oiscs = inventory_struct_channel.objects.filter(sku=sku, channel_code=channel_code)
                if len(oiscs) == 0:
                    oisc = inventory_struct_channel()
                    oisc.user_name = user_name
                    oisc.user_id = user_id
                    oisc.sku = sku
                    oisc.name = pf.name
                    oisc.quantity = quantity
                    oisc.channel_code = channel_code
                    oisc.channel_name = ch.name
                    oisc.save()
                else:
                    oisc = oiscs[0]
                    distributable_quantity = int(oisc.quantity) + int(quantity)
                    oisc.quantity = distributable_quantity
                    oisc.save()

                # 已分配数量
                allocated_quantity = int(ois.ch_quantity) + int(quantity)
                ois.ch_quantity = allocated_quantity
                ois.save()
            except Exception as e:
                rm.code = -1
                rm.message = "exception:" + e.message
                return rm

            oirc = inventory_receipt_channel()
            oirc.sku = sku
            oirc.channel_code = channel_code
            oirc.channel_name = ch.name
            oirc.user_id = user_id
            oirc.user_name = user_name
            oirc.comments = comments
            oirc.price = pf.base_price
            oirc.doc_type = doc_type
            oirc.doc_number = p_number
            oirc.quantity = quantity
            oirc.save()
            stock_data = [{"sku": sku,
                           "web_sku": '',
                           "quantity": quantity,
                           "doc_type": doc_type,
                           "relevant_number": p_number,
                           "options": ""}]

            wi = web_inventory()
            data = wi.web_invs_receipt(stock_data)
            if data["code"] == 0:
                oirc.success_status = '0'
                oirc.message = data["message"]
                oirc.save()
            else:
                oirc.success_status = '1'
                oirc.message = data["message"].encode('raw_unicode_escape')
                oirc.save()
                rm.code = -1
                rm.message = "exception:" + data["message"]
                return rm

        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
            return rm
        return rm


# 库存渠道出库单
class inventory_delivery_channel(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    STATUS_CHOICES = (
        ('0', '执行成功'),
        ('1', '执行失败'),
        ('2', '未执行')
    )
    type = models.CharField(u'Type', max_length=20, default='OIDC', editable=False)
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    channel_code = models.CharField(u'CODE', max_length=128, default='', blank=True)
    channel_name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)
    success_status = models.CharField(u'Status', max_length=40, default='2',
                                      choices=STATUS_CHOICES)
    message = models.CharField(u'message', max_length=512, default='', blank=True, null=True)


class inventory_delivery_channel_controller():
    def add(self, request, p_number, channel_code, doc_type, sku, quantity, comments=''):
        rm = response_message()
        try:
            #with transaction.atomic():
            if request is not None:
                user_id = request.user.id
                user_name = request.user.username
            else:
                user_id = 0
                user_name = 'system'

            try:
                try:
                    ois = inventory_struct.objects.get(sku=sku)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到SKU：' + sku + '的inventory_struct数据'
                    return rm

                try:
                    pf = product_frame.objects.get(sku=sku)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到SKU：' + sku + '的product_frame数据'
                    return rm

                try:
                    ch = channel.objects.get(code=channel_code)
                except Exception as e:
                    logging.critical(u"错误：" + str(e))
                    rm.capture_execption(e)
                    rm.message = '未获取到code：' + channel_code + '的channel数据'
                    return rm

                oiscs = inventory_struct_channel.objects.filter(sku=sku, channel_code=channel_code)
                if len(oiscs) == 0:
                    rm.code = -1
                    rm.message = u'库存结构渠道表不存在该SKU'
                    return rm

                oisc = oiscs[0]
                oisc_qty = int(oisc.quantity)
                distributable_quantity = int(oisc.quantity) - int(quantity)
                if distributable_quantity < 0:
                    distributable_quantity = 0
                    dis_quantity = int(ois.ch_quantity) - oisc_qty
                else:
                    # 分配数量
                    dis_quantity = int(ois.ch_quantity) - int(quantity)
                    if dis_quantity < 0:
                        dis_quantity = 0

                oisc.quantity = distributable_quantity
                oisc.save()
                ois.ch_quantity = dis_quantity
                ois.save()
            except Exception as e:
                logging.debug(str(e))
                rm.code = -1
                rm.message = "exception:" + e.message
                return rm

            oidc = inventory_delivery_channel()
            oidc.sku = sku
            oidc.channel_code = channel_code
            oidc.channel_name = ch.name
            oidc.user_id = user_id
            oidc.user_name = user_name
            oidc.comments = comments
            oidc.price = pf.base_price
            oidc.doc_type = doc_type
            oidc.doc_number = p_number
            oidc.quantity = quantity
            oidc.save()

            stock_data = [{"sku": sku,
                           "web_sku": '',
                           "quantity": quantity,
                           "doc_type": doc_type,
                           "relevant_number": p_number,
                           "options": ""}]

            wi = web_inventory()
            data = wi.web_invs_delivery(stock_data)

            if data["code"] == 0:
                oidc.success_status = '0'
                oidc.message = data["message"]
                oidc.save()
            else:
                oidc.success_status = '1'
                oidc.message = data["message"].encode('raw_unicode_escape')
                oidc.save()
                rm.code = -1
                rm.message = "exception:" + data["message"]
                return rm

        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
            return rm
        return rm


# 库存渠道表初始化
class inventory_initial_channel(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OIIC', editable=False)
    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    channel_code = models.CharField(u'CODE', max_length=128, default='', blank=True)
    channel_name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    price = models.DecimalField(u'PRICE', max_digits=10, decimal_places=2, default=0)

class inventory_operation_log_controller():

    def inventory_operation_logs(self,sku):
        reason_list=[]
        try:
            sql = """
                select id,reason,created_at,user_name,operation_type from wms_inventory_operation_log where sku='%s'
                order by created_at desc
            """ % sku
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                reason_list = namedtuplefetchall(cursor)
        except Exception as e:
            logging.debug('Exception: %s' % e)
        return reason_list


class LockersConfig(models.Model):

    class Meta:
        db_table = 'wms_lockers_config'

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('STANDARD', '普通'),
        ('EXPRESS', '加急'),
        ('EMPLOYEE', '内部'),
        ('FLATRATE', '批量'),
        ('CA_EXPRESS','加急-加拿大')
    )

    glasses_max_limit = models.IntegerField(u'Glasses Max Limit', default=0)  # 仓位最大存储量
    lockers_max_limit = models.IntegerField(u'Lockers Max Limit', default=0)  # 仓位个数最大量
    storage_location = models.CharField(u'Storage Location',max_length=128, default='', null=True) #仓位位置
    is_vender = models.BooleanField(u'Is Vender', default=True) #是否启用vd管理
    ship_direction = models.CharField(u'配送方法', max_length=40, default='STANDARD',
                                      choices=SHIP_DIRECTION_CHOICES)
    lockers_min_limit = models.IntegerField(u'Lockers Min Limit', default=0)  # 仓位最小存储量

    #通告位置名称（DY or SH）查找是否存在此配置信息
    def query_by_id(self, id):
        lockersConfig = LockersConfig.objects.get(id=id)
        return lockersConfig

class Lockers(models.Model):

    class Meta:
        db_table = 'wms_lockers'
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    is_send = models.BooleanField(u'Is Send', default=False)
    vender= models.CharField(u'Vender',max_length=128, default='') #VD
    storage_location = models.CharField(u'Storage Location',max_length=128, default='', null=True) #仓位位置

    locker_num = models.CharField(u'Locker Num',max_length=128, default='', null=True) #仓位编号

    quantity = models.IntegerField(u'Quantity', default=0) #仓位数量

    def query_by_id(self, id):
        lockers = Lockers.objects.get(id=id)
        return lockers

class LockersItem(models.Model):
    class Meta:
        db_table = 'wms_lockers_item'

    lab_number = models.CharField(u'Lab Number', max_length=1024, null=False, blank=False)  # laborder number
    order_number = models.CharField(u'Order Number', max_length=1024, null=False, blank=False)  # laborder order number
    vendor = models.CharField(u'Vendor',max_length=1024, null=False, blank=False)
    storage_location = models.CharField(u'Storage Location',max_length=128, default='', null=True)
    locker_num = models.CharField(u'Locker Num', max_length=128, default='', null=True)   #仓位编号
    create_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)


class locker_controller():

    def get_locker_config(self, storage_location):
        max_glass=0
        try:
           with connections['default'].cursor() as cursor:
            sql = """SELECT lockers_max_limit,glasses_max_limit from wms_lockers_config where storage_location= '%s'
                         """ % storage_location
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                max_locker = item.lockers_max_limit
                max_glass = item.glasses_max_limit
                break

        except Exception as e:
            logging.debug('exception .... %s' % e.message)
        return max_glass

    def get_status_cn(self,status):
        logging.debug(status)
        if status == '':
            status= '新订单'
        if status == 'REQUEST_NOTES':
            status= '出库申请'
        if status == 'FRAME_OUTBOUND':
            status= '镜架出库'
        if status == 'PRINT_DATE':
            status = '镜片生产'
        if status == 'LENS_OUTBOUND':
            status ='镜片出库'
        if status == 'LENS_REGISTRATION':
            status ='来片登记'
        if status == 'LENS_RETURN':
            status='镜片退货'
        if status == 'LENS_RECEIVE':
            status='镜片收货'
        if status == 'ASSEMBLING':
            status='待装配'
        if status == 'ASSEMBLED':
            status='装配完成'
        if status == 'GLASSES_RECEIVE':
            status='成镜收货'

        if status == 'FINAL_INSPECTION':
            status= '终检'
        if status == 'FINAL_INSPECTION_YES':
            status= '终检合格'
        if status == 'FINAL_INSPECTION_NO':
            status= '终检不合格'
        if status == 'GLASSES_RETURN':
            status = '成镜返工'
        if status == 'COLLECTION':
            status ='归集'
        if status == 'PRE_DELIVERY':
            status ='预发货'
        if status == 'PICKING':
            status='已拣配'
        if status == 'ORDER_MATCH':
            status='订单配对'
        if status == 'BOXING':
            status='装箱'
        if status == 'SHIPPING':
            status='已发货'
        if status == 'ONHOLD':
            status='暂停'
        if status == 'CANCELLED':
            status='取消'
        if status == 'REDO':
            status='重做'
        if status == 'R2HOLD':
            status='申请暂停'
        if status == 'R2CANCEL':
            status='申请取消'
        if status == 'CLOSED':
            status='关闭'


        return status

    def locker_add(self, location, max_glass, username, laborder):
        # 默认优先级为最大存储量
        ##判断是否启用VD管理
        locker_config = LockersConfig.objects.get(storage_location=location)
        is_vender = locker_config.is_vender
        try:
            rm = response_message()
            lis = LockersItem.objects.filter(lab_number=laborder.lab_number)
            if len(lis) > 0:
                rm.code = -1
                rm.obj = lis[0]
                rm.message = u'该仓位中存在该订单，请人工确认！'
                return rm
            sql=""
            with connections['pg_oms_query'].cursor() as cursor:
                logging.debug(sql)
                if is_vender == True:
                    sql = """SELECT id, storage_location, locker_num, quantity,vender FROM wms_lockers WHERE
                                              storage_location = '%s' AND quantity < %s and vender='%s' ORDER BY quantity,vender DESC,locker_num+0 ASC """ % (
                    location, max_glass, laborder.vendor)
                elif is_vender ==False:
                    sql = """SELECT id, storage_location, locker_num, quantity,vender FROM wms_lockers WHERE
                                              storage_location = '%s' AND quantity < %s ORDER BY locker_num+0 ASC,quantity DESC """ % (
                    location, max_glass)
                cursor.execute(sql)
                lockers = namedtuplefetchall(cursor)
                locker = lockers[0]

                with transaction.atomic():
                    lockersItem = LockersItem()
                    lockersItem.lab_number = laborder.lab_number
                    lockersItem.order_number = laborder.order_number
                    lockersItem.vendor = laborder.vendor
                    lockersItem.storage_location = locker.storage_location
                    lockersItem.locker_num = locker.locker_num
                    lockersItem.username = username
                    lockersItem.save()
                    # 按照最大存储量优先级最低得放入，locker得qty+1
                    qty = int(locker.quantity) + 1
                    Lockers.objects.filter(storage_location=location, locker_num=locker.locker_num).update(quantity=qty)
            rm.code = 0
            rm.message = u'操作成功！'
            rm.obj = lockersItem
            return rm
        except Exception as e:
            transaction.rollback()
            rm.code = -2
            rm.message = str(e)
            return rm
        # lockersItem = LockersItem()
        # try:
        #     with connections['default'].cursor() as cursor:
        #         sql = """SELECT id,storage_location,locker_num,quantity from wms_lockers where
        #      storage_location= '%s' and quantity<>'%s' order by locker_num asc
        #                             """ % (location,max_glass)
        #         logging.debug(sql)
        #         cursor.execute(sql)
        #         for item in namedtuplefetchall(cursor):
        #             if item.quantity < max_glass:
        #                 # 按照最大存储量优先级最低得放入，locker得qty+1
        #                 lock = Lockers()
        #                 lockers=lock.query_by_id(item.id)
        #                 logging.debug(lockers)
        #                 lockers.quantity = lockers.quantity + 1
        #                 logging.debug(lockers.quantity)
        #                 lockers.save()
        #                 lockersItem.lab_number = laborder.lab_number
        #                 lockersItem.order_number = laborder.order_number
        #                 lockersItem.vendor = laborder.vendor
        #                 lockersItem.storage_location = lockers.storage_location
        #                 lockersItem.locker_num = lockers.locker_num
        #                 lockersItem.username = username
        #                 lockersItem.save()
        #                 break
        # except Exception as e:
        #     logging.debug('exception .... %s' % e)
        # return lockersItem

    # def addItem(self,username,laborder,storage_location,locker_num):
    #     # 保存locker_item
    #     lockersItem = LockersItem()
    #     lockersItem.lab_number = laborder.lab_number
    #     lockersItem.order_number = laborder.order_number
    #     lockersItem.vendor = laborder.vendor
    #     lockersItem.storage_location = storage_location
    #     lockersItem.locker_num = locker_num
    #     lockersItem.username = username
    #     lockersItem.save()
    #     return lockersItem

    def deleteItem(self,lab_number,username=None):
        # 删除locker_item
        rm = response_message()
        try:
            # 获取lockers
            lockersItems = LockersItem.objects.filter(lab_number=lab_number)
            lockersItem = lockersItems[0]
            locker_num = lockersItem.locker_num
            locker=Lockers.objects.filter(locker_num=locker_num, storage_location=lockersItem.storage_location)
            locker_entity=Lockers.objects.get(id=locker[0].id)
            diff_quantity = locker_entity.quantity-1
            if diff_quantity < 0:
                diff_quantity = 0
            locker_entity.quantity= diff_quantity
            locker_entity.save()

            #移除仓位进行日志保存
            lockers_log = LockersLog()
            lockers_log.lab_number=lockersItem.lab_number
            lockers_log.vendor=lockersItem.vendor
            lockers_log.storage_location=lockersItem.storage_location
            lockers_log.locker_num=lockersItem.locker_num
            lockers_log.username=username
            lockers_log.created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lockers_log.save()

            from util.db_helper import DbHelper
            sql = """delete from wms_lockers_item where lab_number='%s'""" % lab_number
            dh = DbHelper()
            dh.execute(sql)
            rm.code = 0
            rm.message = u'仓位移除成功！'
            return rm
        except Exception as e:
            logging.debug('exception .... %s' % e)
            rm.code = -1
            rm.message = str(e)
            return rm

    def redo_job_order(self, lab_number):
        rm = response_message()
        try:
            lockers_items = LockersItem.objects.filter(lab_number=lab_number)
            if len(lockers_items) > 0:
                rm.code = -1
                rm.message = u'请到仓位管理手动处理这个订单的仓位'
                return rm

            rm.code = 0
            rm.message = u'处理成功！'
            return rm
        except Exception as e:
            rm.code = -1
            rm.message = str(e)
            return rm

    def get_locker_num(self, lab_number):
        try:
            lockers_items = LockersItem.objects.filter(lab_number=lab_number)
            if len(lockers_items)>0:
                return lockers_items[0].storage_location +"-"+ lockers_items[0].locker_num
            else:
                return ''
        except Exception as e:
            return ''

    def reset_vendor(self, id, vendor):
        try:
            rm = response_message()
            lockers = Lockers.objects.get(id=id)
            lockers.vender = vendor
            lockers.save()

            rm.code = 0
            rm.message = u'处理成功！'
            return rm
        except Exception as e:
            rm.code = -1
            rm.message = str(e)
            return rm

class LockersLog(base_type):
    class Meta:
        db_table = 'wms_lockers_log'

    lab_number = models.CharField(u'Lab Number', max_length=1024, null=False, blank=False)  # laborder number
    order_number = models.CharField(u'Order Number', max_length=1024, null=False, blank=False)  # laborder order number
    vendor = models.CharField(u'Vendor',max_length=1024, null=False, blank=False)
    storage_location = models.CharField(u'Storage Location',max_length=128, default='', null=True)
    locker_num = models.CharField(u'Locker Num', max_length=128, default='', null=True)   #仓位编号
    create_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)


class HistoryFrameVca(base_type):
    class Meta:
        db_table = 'wms_history_frame_vca'

    SOURCE_CHOICES = (
        ('0', '上传'),
        ('1', '实时')
    )

    batch_number = models.CharField(u'批次号', max_length=128, null=True, blank=True, default='')
    frame = models.CharField(u'镜架 SKU', max_length=128, null=True, blank=True, default='')
    file_path = models.CharField(u'VCA 路径', max_length=128, null=True, blank=True, default='')
    property_list = models.TextField(u'属性集合', max_length=512, default='', null=True, blank=True)
    is_activate = models.BooleanField(u'IS Activate', default=False)
    source = models.CharField(u'来源', max_length=40, default='0', choices=SOURCE_CHOICES)


class ProductFrameVca(base_type):
    class Meta:
        db_table ='wms_product_frame_vca'
    file_path = models.CharField(u'VCA 路径', max_length=128, null=True, blank=True, default='')
    property_list = models.TextField(u'属性集合', max_length=512, default='', null=True, blank=True)
    product_num = models.CharField(u'Product Num', max_length=128, null=True, blank=True, default='')
    batch_number = models.CharField(u'批次号', max_length=128, null=True, blank=True, default='')