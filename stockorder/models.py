# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

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
    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)
    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)


class StockOrder(BaseType):
    class Meta:
        db_table = 'stock_order'

    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Confirm', 'Confirm'),
        ('Processing', 'Processing'),
        ('Cancel', 'Cancel'),
        ('Close', 'Close'),
        ('Finish', 'Finish'),
    )

    stock_order_number = models.CharField(u'Stock Order Number', max_length=128, default='', null=True, blank=True)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    start_date = models.DateTimeField(auto_now=False, null=True)
    process_date = models.DateTimeField(null=True)
    finish_date = models.DateTimeField(auto_now=False, null=True)
    status = models.CharField(u'Status', max_length=20, default='Open', choices=STATUS_CHOICES, null=True, blank=True)
    remaining_qty = models.IntegerField(u'Remaining Qty', default=0)


class StockInRequest(BaseType):
    class Meta:
        db_table = 'stock_in_request'

    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Cancel', 'Cancel'),
        ('Close', 'Close'),
        ('Finish', 'Finish'),
    )
    stock_order_number = models.CharField(u'Stock Order Number', max_length=128, default='', null=True, blank=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True, blank=True)
    status = models.CharField(u'Status', max_length=20, default='Open', choices=STATUS_CHOICES, null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    act_quantity = models.IntegerField(u'Act Quantity', default=0)


class StockStruct(BaseType):
    class Meta:
        db_table = 'stock_struct'

    TYPE_CHOICES = (
        ('PRE_PRODUCT_IN', '预制成品入库'),
    )
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    location = models.CharField(u'Location', max_length=40, default='', null=True)
    inbound_type = models.CharField(u'Inbound Type', max_length=40, default='', null=True, choices=TYPE_CHOICES)


class StockStructLine(BaseType):
    class Meta:
        db_table = 'stock_struct_line'

    TYPE_CHOICES = (
        ('PRE_PRODUCT_IN', '预制成品入库'),
    )
    stock_order_number = models.CharField(u'Stock Order Number', max_length=128, default='', null=True, blank=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
    location = models.CharField(u'Location', max_length=40, default='', null=True)
    inbound_type = models.CharField(u'Inbound Type', max_length=40, default='', null=True, choices=TYPE_CHOICES)


class InterbranchOrder(BaseType):
    class Meta:
        db_table = 'stock_interbranch_order'

    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Printed', 'Printed'),
        ('Fulfilled', 'Fulfilled'),
        ('Cancelled', 'Cancelled'),
        ('Finish', 'Finish'),
    )

    interbranch_order_number = models.CharField(u'Interbranch Order Number', max_length=128, default='', null=True, blank=True)
    warehouse_from = models.CharField(u'Warehouse From', max_length=128, default='', null=True, blank=True)
    location_from = models.CharField(u'Location From', max_length=128, default='', null=True, blank=True)
    warehouse_to = models.CharField(u'Warehouse To', max_length=128, default='', null=True, blank=True)
    location_to = models.CharField(u'Location To', max_length=128, default='', null=True, blank=True)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True, blank=True)
    sku_attribute = models.CharField(u'Sku Attribute', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    start_date = models.DateTimeField(auto_now=False, null=True)
    fulfil_date = models.DateTimeField(null=True)
    finish_date = models.DateTimeField(auto_now=False, null=True)
    status = models.CharField(u'Status', max_length=20, default='Open', choices=STATUS_CHOICES, null=True, blank=True)


class StockBomStruct(BaseType):
    class Meta:
        db_table = 'stock_bom_struct'

    product_sku = models.CharField(u'Product Sku', max_length=128, default='', null=True, blank=True)
    product_qty = models.IntegerField(u'Product Quantity', default=0)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    frame_qty = models.IntegerField(u'Frame Quantity', default=0)
    od_lens_sku = models.CharField(u'OD Lens Sku', max_length=128, default='', null=True, blank=True)
    od_lens_name = models.CharField(u'OD Lens Name', max_length=128, default='', null=True, blank=True)
    od_sph = models.DecimalField(u'OD SPH', max_digits=5, decimal_places=2, default=0)
    od_cyl = models.DecimalField(u'OD CYL', max_digits=5, decimal_places=2, default=0)
    od_lens_qty = models.IntegerField(u'Quantity', default=0)
    os_lens_sku = models.CharField(u'OS Lens Sku', max_length=128, default='', null=True, blank=True)
    os_lens_name = models.CharField(u'OD Lens Name', max_length=128, default='', null=True, blank=True)
    os_sph = models.DecimalField(u'OS SPH', max_digits=5, decimal_places=2, default=0)
    os_cyl = models.DecimalField(u'OS CYL', max_digits=5, decimal_places=2, default=0)
    os_lens_qty = models.IntegerField(u'Quantity', default=0)

