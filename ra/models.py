# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction
from util.base_type import base_type
from util.response import response_message
import logging
import datetime
from util.send_email import SendEmail
from oms.models.order_models import PgOrder

from wms.models import inventory_receipt_control
from oms.controllers.pg_order_controller import pg_order_controller


# Create your models here.
class RaEntity(base_type):
    class Meta:
        db_table = 'ra_entity'

    STATE_CHOICES = (
        ('0', 'Open'),
        ('10', 'Processing'),
        ('90', 'Completed'),
        ('901', 'Closed'),
        ('902', 'Canceled'),
    )
    STATUS_CHOICES = (
        ('0', 'Created'),
        ('10', 'Staging'),
        ('20', 'Label'),
        ('30', 'Stock In'),
        ('40', 'Refund'),
    )
    TYPE_CHOICES = (
        ('CPN', 'Return Coupon'),
        ('RFD', 'Return Refund'),
        ('INS', 'Inspection'),
        ('DMG', 'Damaged'),
        ('RFW', 'Risk Free Warranty'),
        ('RMK', 'Internal Remake'),
    )

    type = models.CharField(u'Type', max_length=20, default='ORAE', editable=False)

    base_entity = models.IntegerField(u'Base Entity', default=0)
    base_type = models.CharField(u'Base Type', max_length=20, default='', editable=False, blank=True)

    state = models.CharField(u'State', max_length=20, default='0', choices=STATE_CHOICES, null=True, blank=True, )
    status = models.CharField(u'Status', max_length=20, default='0', choices=STATUS_CHOICES, null=True, blank=True, )
    ra_type = models.CharField(u'RA Type', max_length=20, default='', choices=TYPE_CHOICES, null=True, blank=True, )

    label_id = models.CharField(u'Label Id', max_length=128, default='', null=True, blank=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    order_number_part = models.CharField(u'Order Number Part', max_length=128, default='', null=True, blank=True)
    customer_name = models.CharField(u'Customer Name', max_length=128, default='', null=True, blank=True)
    ticket_id = models.CharField(u'Ticket #', max_length=128, default='', null=True, blank=True)
    ticket_id_part = models.CharField(u'Ticket # Part', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=1)
    amount = models.DecimalField(u'Amount', max_digits=10, decimal_places=2, default=0)

    tracking_code = models.CharField(u'Tracking Code', max_length=256, default='', null=True, blank=True)
    warehouse_code = models.CharField(u'Warehouse Code', max_length=128, default='', null=True, blank=True)
    warehouse_name = models.CharField(u'Warehouse Name', max_length=128, default='', null=True, blank=True)

    transaction_id = models.CharField(u'Transaction Id', max_length=256, default='', null=True, blank=True)
    location = models.CharField(u'Location', max_length=128, default='', null=True, blank=True)

    is_approved = models.BooleanField(u'Is Approved', default=False)
    is_label = models.BooleanField(u'Is Buy Label', default=False)
    is_stock = models.BooleanField(u'Is Stock', default=False)
    is_refund = models.BooleanField(u'Is Refund', default=False)

    approved_at = models.DateTimeField(u'approved At', null=True, blank=True)
    label_at = models.DateTimeField(u'Buy Label At', null=True, blank=True)
    stock_at = models.DateTimeField(u'Stock At', null=True, blank=True)
    refund_at = models.DateTimeField(u'Refund At', null=True, blank=True)
    email_to = models.CharField(u'Email To', max_length=256, default='', null=True, blank=True)

    closed_at = models.DateTimeField(u'Closed At', null=True, blank=True)
    completed_at = models.DateTimeField(u'Completed At', null=True, blank=True)
    canceled_at = models.DateTimeField(u'Canceled At', null=True, blank=True)

    def get_items(self):
        itms = RaItem.objects.filter(base_entity=self.id)
        return itms


class RaItem(base_type):
    class Meta:
        db_table = 'ra_item'

    type = models.CharField(u'Type', max_length=20, default='RAEL', editable=False)

    base_entity = models.IntegerField(u'Base Entity', default=0)
    frame = models.CharField(u'Frame SKU', max_length=128, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=1)
    price = models.DecimalField(u'Price', max_digits=10, decimal_places=2, default=0)


class RaController:
    def add(self, request, data_dict):
        rm = response_message()
        user_id = 0
        user_name = 'System'
        if request:
            user_id = request.user.id
            user_name = request.user.username

        try:
            with transaction.atomic():
                ra_entity = RaEntity()
                ra_entity.__dict__.update(**data_dict)
                ra_entity.user_id = user_id
                ra_entity.user_name = user_name

                order_number = ra_entity.order_number
                pgo = PgOrder.objects.get(order_number=order_number)

                # 2019.12.23 by guof.
                # 增加基于 RMK 类型的特殊判断
                # 如果是 RMK 类型，Amount 必须为0
                if ra_entity.ra_type == 'RMK':
                    if float(ra_entity.amount) <> float(0):
                        rm.code = -200
                        rm.message = "If RaType is 'RMK', Amount must be zero!"
                        return rm

                if float(ra_entity.amount) > float(pgo.total_paid):
                    rm.code = -100
                    rm.message = "Amount must Less than or equal to order's total_paid!!!"
                    return rm

                items = data_dict['items']
                items_subtotal = 0
                for item in items:
                    items_subtotal += item.get('price', 0)
                if float(ra_entity.amount) > float(items_subtotal):
                    rm.code = -100
                    rm.message = "Amount must Less than or equal to order's items subtotal!!!"
                    return rm

                ra_entity.save()
                for item in items:
                    ra_item = RaItem()
                    item.pop('id')
                    ra_item.__dict__.update(**item)

                    poc = pg_order_controller()
                    req = {
                        "pg_frame": item['frame']
                    }
                    rqm = poc.get_lab_frame(req)
                    ra_item.frame = rqm.obj['lab_frame']
                    ra_item.base_entity = ra_entity.id
                    ra_item.save()

                lc = RaLogController()
                lc.add(request, ra_entity.id, ra_entity.type, 'NEW', 'Created')

        except Exception as ex:
            logging.error(str(ex))
            rm.capture_execption(ex)

        return rm

    def action(self, request, data_dict):
        rm = response_message()
        user_id = 0
        user_name = 'System'
        if request:
            user_id = request.user.id
            user_name = request.user.username

        logging.debug('Action')
        logging.debug('----------------------------------------------------------------------')
        logging.debug(data_dict)
        entity = data_dict.get('entity', None)
        try:
            if entity:
                id = entity['id']
                action = data_dict['action']
                email = data_dict['email']
                tracking_code = data_dict['tracking_code']
                location = data_dict['location']
                transaction_id = data_dict['transaction_id']
                comments = data_dict['comments']
                obj = RaEntity.objects.get(id=id)

                nw = datetime.datetime.now()
                lc = RaLogController()

                ra_type = entity['ra_type']

                if action == 'APPROVE':  # state value = 10
                    if obj.state == '10':
                        rm.code = 10
                        rm.message = 'Ra state is [Processing], nothing to do!'
                        return rm

                    if obj.is_approved:
                        rm.code = 10
                        rm.message = 'Ra status is [is_approved], nothing to do!'
                        return rm

                    obj.state = '10'
                    obj.status = '10'
                    obj.is_approved = True
                    obj.approved_at = nw

                    lc.add(request, obj.id, obj.type, action, action, comments)

                    if ra_type == 'CPN':
                        obj.email_to = email
                        email_subject = '[%s]-Coupon Create Notice' % entity['label_id']
                        email_text = 'Coupon Amount:[$%s][%s]' % (entity['amount'], entity['created_at'])

                        se = SendEmail()
                        se.send_email(obj.email_to, email_subject, email_text)
                        lc.add(request, obj.id, obj.type, 'EMAIL_TO', 'Email TO: %s' % obj.email_to, email_text)

                if action == 'BUY_LABEL':  # status value = 20
                    if obj.state != '10':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm
                    if obj.is_label:
                        rm.code = 20
                        rm.message = 'Ra status is [Label], nothing to do!'
                        return rm

                    obj.status = '20'
                    obj.is_label = True
                    obj.label_at = nw
                    obj.tracking_code = tracking_code
                    lc.add(request, obj.id, obj.type, action, action, comments)

                if action == 'STOCK_IN':  # status value = 20
                    if obj.state != '10':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm
                    if obj.is_stock:
                        rm.code = 30
                        rm.message = 'Ra status is [STOCK_IN], nothing to do!'
                        return rm

                    obj.status = '30'
                    obj.is_stock = True
                    obj.stock_at = nw
                    obj.location = location

                    logging.debug('location: %s' % location)

                    # 调用入库
                    irc = inventory_receipt_control()
                    warehouse_code = 'USRW01'
                    items = obj.get_items()
                    for item in items:
                        doc_number = "%s-%s" % (obj.id, item.id)
                        irc.add(request, doc_number, warehouse_code, item.frame, 0, 'REFUNDS_IN', item.quantity)

                    if ra_type != 'CPN':
                        obj.email_to = email
                        email_subject = '[%s]-Refund Notice' % entity['label_id']
                        email_text = 'Refund Amount:[$%s][%s]' % (entity['amount'], entity['created_at'])

                        se = SendEmail()
                        se.send_email(obj.email_to, email_subject, email_text)
                        lc.add(request, obj.id, obj.type, 'EMAIL_TO', 'Email TO: %s' % obj.email_to, email_text)

                    if ra_type == 'RMK':
                        rm = self.refund_ra(obj)

                if action == 'REFUND':  # status value = 20
                    if obj.state != '10':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm

                    if obj.ra_type == 'CPN':
                        rm.code = 33
                        rm.message = 'Ra Type is [CPN], nothing to do!'
                        return rm

                    if not obj.is_stock:
                        rm.code = 30
                        rm.message = 'Ra status must be [STOCK_IN], nothing to do!'
                        return rm
                    if obj.is_refund:
                        rm.code = 40
                        rm.message = 'Ra status is [REFUND], nothing to do!'
                        return rm

                    rm = self.refund_ra(obj)

                    lc.add(request, obj.id, obj.type, action, action, comments)

                if action == 'COUPON':  # status value = 20
                    if obj.state != '10':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm

                    if obj.ra_type != 'CPN':
                        rm.code = 33
                        rm.message = 'Ra Type must be [CPN], nothing to do!'
                        return rm

                    if obj.is_refund:
                        rm.code = 40
                        rm.message = 'Ra status is [REFUND], nothing to do!'
                        return rm

                    obj.transaction_id = transaction_id

                    rm = self.refund_ra(obj)

                    lc.add(request, obj.id, obj.type, action, action, comments)

                if action == 'CLOSE':  # status value = 20
                    if obj.state != '10':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm

                    obj.state = '901'
                    obj.closed_at = nw

                    lc.add(request, obj.id, obj.type, action, action, comments)

                if action == 'CANCEL':  # status value = 20
                    if obj.state != '0':
                        rm.code = 10
                        rm.message = 'Ra state must be [Processing], nothing to do!'
                        return rm

                    obj.state = '902'
                    obj.canceled_at = nw

                    lc.add(request, obj.id, obj.type, action, action, comments)

                obj.comments += '\r\n' + comments
                obj.save()

        except Exception as ex:
            rm.capture_execption(ex)
            logging.error(str(ex))
        return rm

    def refund_ra(self, obj):
        nw = datetime.datetime.now()
        rm = response_message()

        data = {}
        data['order_number'] = obj.order_number
        poc = pg_order_controller()
        rm = poc.refund(data)

        if rm.code != 0:
            return rm

        obj.state = '90'
        obj.status = '40'
        obj.is_refund = True
        obj.refund_at = nw

        return rm


class RaLog(base_type):
    class Meta:
        db_table = 'ra_log'

    type = models.CharField(u'Type', max_length=20, default='ORAL', editable=False)

    base_entity = models.IntegerField(u'Base Entity', default=0)
    base_type = models.CharField(u'Base Type', max_length=20, default='', editable=False, blank=True)
    action = models.CharField(u'Action', max_length=128, default='', null=True, blank=True)
    action_value = models.CharField(u'Action Value', max_length=128, default='', null=True, blank=True)


class RaLogController:
    def add(self, request, entity_id, type, action, action_value, comments=''):
        user_id = 0
        user_name = 'System'
        if request:
            user_id = request.user.id
            user_name = request.user.username
        lo = RaLog()
        lo.user_id = user_id
        lo.user_name = user_name
        lo.base_entity = entity_id
        lo.base_type = type
        lo.action = action
        lo.action_value = action_value
        lo.comments = comments
        lo.save()

    def get_log_list(self, entity_id, type):
        logs = RaLog.objects.filter(base_entity=entity_id, base_type=type).order_by('-id')
        return logs
