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


class AccsOrder(BaseType):
    class Meta:
        db_table = 'accs_order'
    SHIP_DIRECTION_CHOICES = (
        ('STANDARD', '普通'),
        ('EXPRESS', '加急'),
        ('EMPLOYEE', '内部'),
        ('FLATRATE', '批量'),
        ('CA_EXPRESS','加急-加拿大')
    )
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('RePick', 'RePick'),
        ('Picking', 'Picking'),
        ('Picked', 'Picked'),
        ('QCed', 'QCed'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('onHold', 'onHold'),
        ('Cancelled', 'Cancelled'),
        ('Closed', 'Closed')
    )
    WAREHOUSE_CHOICES = (
        ('AC01', '产品附件库-丹阳'),
        ('AC02', '产品附件库-上海'),
        ('US-AC01', 'US  AC Warehouse 01')
    )
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OACO', editable=False)

    base_entity = models.CharField(u'基础单据', max_length=128, default='', null=True, blank=True)
    base_type = models.CharField(u'基础单据类型', max_length=20, default='', editable=False)

    accs_order_number = models.CharField(u'Accs Order Number', max_length=128, default='', null=True, blank=True)
    sku = models.CharField(u'SKU', max_length=128, default='', null=True, blank=True)
    name = models.CharField(u'SKU Name', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    repick_quantity = models.IntegerField(u'Repick Quantity', default=0)
    order_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    shipping_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    assign_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    pick_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    qc_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    pack_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    ship_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    close_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    hold_date = models.DateTimeField(auto_now=False, null=True, blank=True)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True, blank=True, choices=WAREHOUSE_CHOICES)
    location = models.CharField(u'Location', max_length=40, default='', null=True, blank=True)
    last_status = models.CharField(u'当前状态', max_length=128, null=True, blank=True, default='')
    status = models.CharField(u'Status', max_length=20, default='Open', choices=STATUS_CHOICES, null=True, blank=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    is_rx_have = models.BooleanField(u'Rx Have', default=False)
    ship_direction = models.CharField(u'配送方法', max_length=40, default='STANDARD',
                                      choices=SHIP_DIRECTION_CHOICES)
    image = models.CharField(u'Image', max_length=255, default='', null=True, blank=True)
    thumbnail = models.CharField(u'Thumbnail', max_length=255, default='', null=True, blank=True)


class AccsOrderTracking(BaseType):
    class Meta:
        db_table = 'accs_order_tracking'

    order_number = models.CharField(u'Order Number', max_length=128, null=False, blank=False, default='')
    action = models.CharField(u'Action', max_length=128, null=True, blank=True, default='')

    def add_order_tracking(self, order_number, user_id, user_name, action, flag=True, comments=''):
        if not flag:
            user_id = 0
            user_name = 'system'

        self.order_number = order_number
        self.user_id = user_id
        self.user_name = user_name
        self.action = action
        self.comments = comments
        self.save()


class AccsOrderRequestNotes(BaseType):
    class Meta:
        db_table = 'accs_order_request_notes'

    WAREHOUSE_CHOICES = (
        ('AC01', '产品附件库-丹阳'),
        ('AC02', '产品附件库-上海'),
        ('W02', '镜架库-上海'),
        ('US-AC01', 'US  AC Warehouse 01')
    )
    type = models.CharField(u'类型', max_length=20, default='AORN', editable=False)
    accsorder_id = models.IntegerField(u'Entity ID', default=0)
    accs_order_number = models.CharField(u'Accs Order Number', max_length=128, default='', blank=True, null=True)
    count = models.IntegerField(u'Count', default=0)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True, blank=True,
                                 choices=WAREHOUSE_CHOICES)
    last_flag = models.BooleanField(default=False)


class AccsOrderRequestNotesLine(BaseType):
    class Meta:
        db_table = 'accs_order_request_notes_line'

    WAREHOUSE_CHOICES = (
        ('AC01', '产品附件库-丹阳'),
        ('AC02', '产品附件库-上海'),
        ('W02', '镜架库-上海'),
        ('US-AC01', 'US  AC Warehouse 01')
    )
    type = models.CharField(u'类型', max_length=20, default='AORL', editable=False)
    accs_order_number = models.CharField(u'Accs Order Number', max_length=128, default='', blank=True, null=True)
    base_entity = models.IntegerField(u'Entity ID', default=0)
    accsorder_id = models.IntegerField(u'Entity ID', default=0)
    index = models.IntegerField(u'Index', default=0)
    sku = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True, blank=True,
                                 choices=WAREHOUSE_CHOICES)

    def add_accsorder_reques_notes_line(self, accs_order_number, base_entity, accsorder_id, sku, quantity, warehouse, user_name, flag=True):
        if not flag:
            user_id = 0
            user_name = 'system'

        self.accs_order_number = accs_order_number
        self.base_entity = base_entity
        self.accsorder_id = accsorder_id
        self.sku = sku
        self.quantity = quantity
        self.warehouse = warehouse
        self.user_name = user_name
        self.save()

        accsorder_requestnote = AccsOrderRequestNotes.objects.get(id=base_entity)
        count = accsorder_requestnote.count + 1
        accsorder_requestnote.count = count
        accsorder_requestnote.save()


class AccsOrderDeliveryLine(BaseType):
    class Meta:
        db_table = 'accs_order_delivery_line'

    sku = models.CharField(u'SKU', max_length=40, default='', null=True)
    name = models.CharField(u'NAME', max_length=128, default='', blank=True)
    base_entity = models.IntegerField(u'Entity ID', default=0)
    quantity = models.DecimalField(u'Quantity', max_digits=10, decimal_places=0, default=0)
    accs_order_number = models.CharField(u'单号', max_length=128, default='', null=True)
    warehouse = models.CharField(u'Warehouse Code', max_length=40, default='', null=True)
