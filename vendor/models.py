# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
# Base Type
from util.base_type import base_type

from oms.models.choices_models import *


class corp_apps_info(base_type):
    def __str__(self):
        return '%s-%s' % (self.vendor_code, self.corp_id)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OCAI', editable=False)

    vendor_code = models.CharField(u'Vendor Code', max_length=128, default='', null=True, blank=True)
    vendor_name = models.CharField(u'Vendor Name', max_length=128, default='', null=True, blank=True)
    corp_id = models.CharField(u'Corp ID', max_length=36, default='', null=True, blank=True)
    app_key = models.CharField(u'App Key', max_length=20, default='', null=True, blank=True)
    app_secret = models.CharField(u'App Secret', max_length=64, default='', null=True, blank=True)


class order_status_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OOSB', editable=False)

    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    reference_code = models.CharField(u'Reference Code', max_length=128, default='', null=True, blank=True)
    reference_code_2 = models.CharField(u'Reference Code 2', max_length=128, default='', null=True, blank=True)
    status_code = models.CharField(u'Status Code', max_length=36, default='', null=True, blank=True)
    status_value = models.CharField(u'Status Value', max_length=20, default='', null=True, blank=True)
    status_updated_at = models.CharField(u'Updated At', max_length=36, default='', null=True, blank=True)

    is_sync = models.BooleanField(u'Is Sync', default=False)


class wc_order_status(order_status_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OSWC', editable=False)


# 产品基本信息
class product_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PRDB', editable=False)

    parent = models.ForeignKey('self', models.CASCADE,
                               blank=True,
                               null=True, )

    product_type = models.CharField(u'PRODUCT TYPE', max_length=15, default='FRAME',
                                    choices=PRODUCT_TYPE_CHOICES)

    sku = models.CharField(u'SKU', max_length=40, default='', unique=True, null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    base_price = models.DecimalField(u'Base PRICE', max_digits=10, decimal_places=2, default=0)


class lens(product_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='VLNS', editable=False)

    index = models.CharField(u'Lens Index', max_length=20, default='1.56',
                             choices=LENS_INDEX_CHOICES)

    quantity = models.IntegerField(u'Quantity', default=-1)

    lens_type = models.CharField(u'Lens type', max_length=20, default='0',
                                 choices=LENS_TYPE_CHOICES)

    material = models.CharField(u'Material', max_length=128, default='', null=True, blank=True)
    brand = models.CharField(u'Brand', max_length=128, default='', null=True, blank=True)
    series = models.CharField(u'Series', max_length=128, default='', null=True, blank=True)
    base_sku = models.CharField(u'Base SKU', max_length=128, default='', null=True)
    base_price = models.DecimalField(u'Base Price', max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(u'Final Price', max_digits=10, decimal_places=2, default=0)
    vd_lens_sku = models.CharField(u'Vendor Lens SKU', max_length=40, default='', null=True, blank=True)
    vd_lens_name = models.CharField(u'Vendor Lens Name', max_length=128, default='', blank=True)
    vendor_code = models.CharField(u'Vendor Code', max_length=128, default='', null=True, blank=True)
    vendor_name = models.CharField(u'Vendor Name', max_length=128, default='', null=True, blank=True)

    bar_code = models.CharField(u'Bar Code', max_length=128, default='', null=True, blank=True)

    priority = models.IntegerField(u'priority', default=100)


class lens_order(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='LENO', editable=False)
    status = models.CharField(u'Status', max_length=128, default='', blank=True, null=True)
    base_entity = models.IntegerField(u'Sequence', default=0)
    base_type = models.CharField(u'Type', max_length=20, default='', editable=False)
    order_number = models.CharField(u'Order Number', max_length=128, default='', blank=True, null=True, editable=False)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', blank=True, null=True, editable=False)
    lens_sku = models.CharField(u'SKU', max_length=40, default='', null=True, blank=True)
    lens_name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    lens_index = models.CharField(u'Lens Index', max_length=20, default='1.56',
                                  choices=LENS_INDEX_CHOICES)
    vd_lens_sku = models.CharField(u'VD Lens SKU', max_length=40, default='', null=True, blank=True)
    vd_lens_name = models.CharField(u'VD Lens NAME', max_length=128, default='', blank=True)

    quantity = models.IntegerField(u'数量', default=1)

    rl_identification = models.CharField(u'RL Identification', max_length=20, default='R',
                                         choices=IDENTIFICATION_CHOICES)

    sph = models.DecimalField(u'光度(OD)', max_digits=5, decimal_places=2, default=0)
    cyl = models.DecimalField(u'散光(OD)', max_digits=5, decimal_places=2, default=0)
    axis = models.DecimalField(u'轴位(OD)', max_digits=5, decimal_places=0, default=0)
    pd = models.DecimalField(u'瞳距(OD)', max_digits=5, decimal_places=2, default=0)

    # Prescription extends

    add = models.DecimalField(u'渐进(OD)', max_digits=5, decimal_places=2, default=0)
    prism = models.DecimalField(u'棱镜(OD)', max_digits=5, decimal_places=2, default=0)
    base = models.CharField(u'方向(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)
    prism1 = models.DecimalField(u'棱镜(OD)', max_digits=5, decimal_places=2, default=0)
    base1 = models.CharField(u'方向(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)

    vendor = models.CharField(u'Vendor', max_length=128, null=True, blank=True, default='0', choices=VENDOR_CHOICES)


class distribute_log(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='DLOG', editable=False)
    status = models.CharField(u'Status', max_length=128, default='', blank=True, null=True)
    base_entity = models.IntegerField(u'Base Entity', default=0)
    base_type = models.CharField(u'Type', max_length=20, default='')
    order_number = models.CharField(u'Order Number', max_length=128, default='', blank=True, null=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', blank=True, null=True)
    lens_sku = models.CharField(u'Lens SKU', max_length=40, default='', null=True, blank=True)
    lens_name = models.CharField(u'Lens Name', max_length=128, default='', null=True, blank=True)
    lens_index = models.CharField(u'Lens Index', max_length=20, default='1.56',
                                  choices=LENS_INDEX_CHOICES)
    vd_lens_sku = models.CharField(u'Vendor Lens SKU', max_length=40, default='', null=True, blank=True)
    vd_lens_name = models.CharField(u'Vendor Lens Name', max_length=128, default='', blank=True)

    quantity = models.IntegerField(u'Quantity', default=1)

    vendor = models.CharField(u'Vendor', max_length=128, null=True, blank=True, default='0', choices=VENDOR_CHOICES)


class distribute_configuration(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='DCFG', editable=False)

    key = models.CharField(u'Key', max_length=255, default='', null=True, blank=True)
    value = models.CharField(u'Value', max_length=1024, default='', null=True, blank=True)


class wx_product_contrast(models.Model):
    CHANNEL_CHOICES = (
        ('FH15', 'FH15'),
        ('FH17', 'FH17'),
        ('FH19', 'FH19'),
        ('FH21', 'FH21'),
        ('OFFICE', 'OFFICE'),
    )

    LENS_TYPE_CHOICES = (
        ('SINGLE_LIGHT', '单光'),
        ('DOUBLE_LIGHT', '双光'),
        ('PROGRESSIVE', '渐进'),
        ('IN_PROGRESSIVE', '内渐进'),
        ('ANTIFATIGUE', '抗疲劳'),
        ('PAN_FOCUS', '全焦点'),
        ('T_LIGHT', '三光'),
    )

    MATERIALS_CHOICES = (
        ('RESINOUS', 'resinous'),
    )

    code = models.CharField(u'伟星产品代码', max_length=128, unique=True, default='', blank=True)
    act_lens_sku = models.CharField(u'实际镜片SKU', max_length=64, default='', null=True, blank=True)
    channel = models.CharField(u'通道', max_length=32, default='FH15', null=True, choices=CHANNEL_CHOICES)
    lens_type = models.CharField(u'镜片类型', max_length=32, default='SINGLE_LIGHT', null=True, choices=LENS_TYPE_CHOICES)
    index = models.DecimalField(u'折射率', max_digits=5, decimal_places=3, default=0)
    materials = models.CharField(u'镜片材质', max_length=32, default='RESINOUS', null=True, choices=MATERIALS_CHOICES)
    wx_name = models.CharField(u'伟星品名', max_length=256, default='', null=True, blank=True)
    name = models.CharField(u'智镜品名', max_length=256, default='', null=True, blank=True)


# 五彩镜片
class wc_lens(models.Model):
    code = models.CharField(u'五彩产品代码', max_length=128, unique=True, default='', blank=True)
    lab_lens_sku = models.CharField(u'工厂镜片SKU', max_length=64, default='', null=True, blank=True)
    index = models.DecimalField(u'折射率', max_digits=5, decimal_places=2, default=0)
    material_sku = models.CharField(u'镜片材质', max_length=64, default='', null=True)
    material_name = models.CharField(u'镜片材质名称', max_length=256, default='', null=True)
    product_sku = models.CharField(u'五彩产品sku', max_length=64, default='', null=True, blank=True)
    product_name = models.CharField(u'品名', max_length=256, default='', null=True, blank=True)
    product_can_add = models.BooleanField(u'是否支持ADD', default=False)
    product_channel_range = models.CharField(u'产品支持的通道范围', max_length=256, default='', null=True, blank=True)
    product_assemble_height_range = models.CharField(u'产品支持的最小瞳高范围', max_length=256, default='', null=True, blank=True)
    diamater = models.CharField(u'直径范围', max_length=256, default='', null=True, blank=True)
    base_bending = models.CharField(u'基弯范围', max_length=256, default='', null=True, blank=True)
    price = models.CharField(u'价格', max_length=64, default='', null=True, blank=True)


class wx_product_relationship(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='WXPR', editable=False)

    sku = models.CharField(u'SKU', max_length=40, default='', unique=True, null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    wx_sku = models.CharField(u'WX SKU', max_length=40, default='', null=True, blank=True)
    wx_name = models.CharField(u'WX NAME', max_length=128, default='', null=True, blank=True)


class LensSpecmap(base_type):
    class Meta:
        db_table = 'vender_lens_specmap'

    TECHNOLOGY_CHOICES=(
        ('COATING', u'AR'),
        ('DESIGN', u'设计'),
        ('TINT', u'染色'),
        ('CHANNEL', u'通道'),
        ('OTHER', u'其它')
    )
    ACTIVE_CHOICES=(
        ('ACTIVE', u'Active'),
        ('UNACTIVE', u'unActive')
    )
    inner_code = models.CharField(u'Inner Code', max_length=128, default='', null=True, blank=True)
    inner_name = models.CharField(u'Inner Name', max_length=128, default='', null=True, blank=True)
    vendor = models.CharField(u'Vendor', max_length=128, default='', null=True, blank=True)
    outer_code = models.CharField(u'Inner Code', max_length=128, default='', null=True, blank=True)
    outer_name = models.CharField(u'Inner Name', max_length=128, default='', null=True, blank=True)
    technology_type = models.CharField(u'Technology Type', max_length=128, default='', null=True, blank=True, choices=TECHNOLOGY_CHOICES)
    active = models.CharField(u'Active', max_length=128, default='UNACTIVE', null=True, blank=True, choices=ACTIVE_CHOICES)


class WxMetaProductRelationship(base_type):
    addStart = models.DecimalField(u'addStart', max_digits=5, decimal_places=2, default=0)
    addEnd = models.DecimalField(u'addEnd', max_digits=5, decimal_places=2, default=0)
    brand = models.CharField(u'brand', max_length=40, default='白包装', null=True, blank=True)
    customerId = models.CharField(u'customerId', max_length=128, default='', null=True, blank=True)
    cylStart = models.DecimalField(u'cylStart', max_digits=5, decimal_places=2, default=0)
    cylEnd = models.DecimalField(u'cylEnd', max_digits=5, decimal_places=2, default=0)
    rate = models.CharField(u'rate', max_length=20, default='', null=True, blank=True)
    sphStart = models.DecimalField(u'sphStart', max_digits=5, decimal_places=2, default=0)
    sphEnd = models.DecimalField(u'sphEnd', max_digits=5, decimal_places=2, default=0)
    zsl = models.CharField(u'zsl', max_length=20, default='', null=True, blank=True)
    defName = models.CharField(u'defName', max_length=20, default='', null=True, blank=True)
    dl = models.CharField(u'dl', max_length=20, default='单光', null=True, blank=True)
    isLr = models.CharField(u'isLr', max_length=20, default='0', null=True, blank=True)
    lenInputType = models.CharField(u'lenInputType', max_length=20, default='', null=True, blank=True)
    lentype = models.CharField(u'lentype', max_length=20, default='', null=True, blank=True)
    price = models.DecimalField(u'price', max_digits=5, decimal_places=2, default=0)
    productId = models.CharField(u'productId', max_length=40, default='', null=True, blank=True)
    productName = models.CharField(u'productName', max_length=40, default='', null=True, blank=True)
    sku = models.CharField(u'SKU', max_length=40, default='', blank=True, null=True)
    class Meta:
        db_table = 'vendor_wx_meta_product_relationship'


class WxOrderStatus(order_status_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OSWX', editable=False)