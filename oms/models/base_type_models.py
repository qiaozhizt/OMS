# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class BaseType(models.Model):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='BAMO', editable=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'SEQUENCE', default=0)
    is_enabled = models.BooleanField(u'IS Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderBaseTypeExtends(models.Model):
    class Meta:
        abstract = True

    CHANNEL_CHOICES = (
        ('', 'NULL'),
        ('FH15', 'FH15'),
        ('FH17', 'FH17'),
        ('FH19', 'FH19'),
        ('FH21', 'FH21'),
    )
    COATINGS_CHOICES = (
        ('HMC', 'HMC'),
        ('HC', 'HC'),
        ('SHMC', 'SHMC'),
    )
    ORDERTYPE_CHOICES = (
        ('STOCK_LENS', 'Stock Lens'),
        ('RX_LENS', 'Rx Lens'),
        ('TINT_LENS', 'Tint Lens'),
        ('PRE_MAKE', 'Pre Make'),
    )

    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)  # , unique=True)  # 该属性必须唯一
    priority = models.IntegerField(u'Priority', default=4)
    tag = models.CharField(u'Tag', max_length=128, default='WEBSITE', null=True, blank=True)

    lens_seght = models.IntegerField(u'LENS SEGHT', default=0)
    asmbl_seght = models.IntegerField(u'ASMBL SEGHT', default=0)

    lens_width = models.IntegerField(u'Lens Width', default=0)
    bridge = models.IntegerField(u'Bridge', default=0)
    temple_length = models.IntegerField(u'Temple Length', default=0)

    lens_height = models.IntegerField(u'Lens Height', default=0)
    is_has_nose_pad = models.BooleanField(u'有无鼻托', default=None)
    pal_design_sku = models.CharField(u'设计编码', max_length=128, default='', null=True, blank=True)
    pal_design_name = models.CharField(u'设计', max_length=512, default='', null=True, blank=True)

    comments_inner = models.TextField(u'内部备注', max_length=1024, default='', null=True, blank=True)
    comments_ship = models.TextField(u'发货', max_length=1024, default='', null=True, blank=True)
    frame_type = models.CharField(u'框型', max_length=512, default='', null=True, blank=True)
    color = models.CharField(u'颜色', max_length=512, default='', null=True, blank=True)

    # 为渐进镜片定义的瞳高字段
    lab_seg_height = models.CharField(u'加工瞳高', max_length=64, default='', null=True, blank=True)
    assemble_height = models.CharField(u'装配瞳高', max_length=32, default='', null=True, blank=True)
    # 为平顶双光镜片定义的子镜高度字段
    sub_mirrors_height = models.CharField(u'子镜高度', max_length=16, default='', null=True, blank=True)
    # 镜片的其他特殊处理要求
    special_handling = models.CharField(u'加工要求', max_length=512, default='', null=True, blank=True)
    # 为美薄处理定义的相关字段 与上面的special_handling不同
    special_handling_sku = models.CharField(u'美薄处理编码', max_length=128, default='', null=True, blank=True)
    special_handling_name = models.CharField(u'美薄处理', max_length=512, default='', null=True, blank=True)
    # 通道字段
    channel = models.CharField(u'通道', max_length=32, default='', null=True, blank=True, choices=CHANNEL_CHOICES)

    # 是否同步到MRP
    is_sync = models.BooleanField(u'是否同步到MRP', default=0,  null=False, blank=False)
    # 终检技术指标增加字段
    clipon_qty = models.IntegerField(u'Clipon', default=0)
    coatings = models.CharField(u'膜层', max_length=32, default='HMC', choices=COATINGS_CHOICES)
    order_type = models.CharField(u'订单分类', max_length=32, default='', choices=ORDERTYPE_CHOICES)

    delivered_at = models.DateTimeField(u'DELIVERED AT', null=True, blank=True)

    @property
    def get_pal_design_sku(self):
        try:
            if float(self.od_add) > 0 or float(self.os_add) > 0:
                return self.pal_design_sku
            else:
                return "null"
        except Exception as e:
            return "-"

    @property
    def get_has_prism(self):
        if (abs(float(self.od_prism)) > 0 and abs(float(self.os_prism)) == 0) \
                or (abs(float(self.od_prism)) == 0 and abs(float(self.os_prism)) > 0):
            return 1
        elif abs(float(self.od_prism)) > 0 and abs(float(self.os_prism)) > 0:
            return 2
        else:
            return 0

    @property
    def get_strong_cyl(self):
        if self.lens_type == 'K':
            if abs(float(self.od_cyl)) > 2.0 or abs(float(self.os_cyl)) > 2.0:
                return True
            else:
                return False
        else:
            return False

    @property
    def get_has_tint(self):
        if self.tint_sku in ('RS-H', 'RS-C', 'RS-L'):
            return 1
        elif self.tint_sku in ('RJ-H', 'RJ-C', 'RJ-L'):
            return 2
        else:
            return 0

    @property
    def get_lens_quantity(self):
        return 2 * self.quantity



class construction_voucher_base(BaseType):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OBCB', editable=False)

    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True, unique=True)

    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)
    print_times = models.IntegerField(u'Print Time', default=1)
