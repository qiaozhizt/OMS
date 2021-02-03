# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import logging
from pg_oms.settings import MRP_BASE_URL

from util.response import response_message

from oms.models.order_models import LabOrder,PgOrder,PgOrderItem
from oms.models.ordertracking_models import OrderTracking
from oms.models.application_models import OperationLog
from oms.controllers.lab_order_controller import lab_order_controller
import requests
import json
import time
from django.db import connections
from util.db_helper import *

# Create your models here.

class tracking_lab_order_controller:

    def __tracking_extends(self, order_number, sku, order_date, lab_order_entity, user_id, username, action,
                           action_value, remark=''):

        rm = response_message()

        try:
            ot = OrderTracking()
            ot.order_number = order_number
            ot.sku = sku
            ot.order_date = order_date
            ot.lab_order_entity = lab_order_entity.id
            ot.user_entity = user_id
            ot.username = username
            ot.action = action
            ot.action_value = action_value
            ot.remark = remark
            ot.save()

            try:
                PgOrderItem.objects.filter(id=lab_order_entity.base_entity).update(lab_status=action)
                PgOrder.objects.filter(order_number=lab_order_entity.order_number).update(lab_status=action)
            except:
                pass

            '''
            rm.code = 0
            rm.message = ''
            # 推送到MRP
            logging.debug('开始推送到MRP')
            url = MRP_BASE_URL + 'api/JobTracking/'
            values = {}
            user_entity_id = str(ot.user_entity.id)
            values['user_id'] = user_entity_id
            values['user_name'] = username
            values['comments'] = ot.remark
            values['order_number'] = ot.lab_order_entity.order_number
            values['entity_id'] = ot.id
            values['entity_created_at'] = str(ot.create_at)
            values['lab_number'] = ot.order_number
            values['status'] = ot.action_value
            values['action'] = ot.action
            values['action_value'] = ot.action_value
            values['frame'] = ot.sku
            values['lens_sku'] = ot.sku

            headers = {'Content-Type': 'application/json'}
            data = json.dumps(values)  # 数据进行编码
            logging.debug('valus:%s' % data)
            req = requests.post(url=url, data=data, headers=headers)
            resp = req.text
            respjs = json.loads(resp)
            if respjs['code'] == 200:
                logging.debug(respjs['message'])
                ot.is_sync = 1
                ot.save()
            '''
        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)

        return rm

    def tracking(self, lab_order_entity, user_entity, action, action_value='', remark=''):
        rm = response_message()

        try:
            order_number = lab_order_entity.lab_number
            if action == 'LENS_OUTBOUND':
                sku = lab_order_entity.act_lens_sku
            else:
                sku = lab_order_entity.frame
            order_date = lab_order_entity.order_date

            if user_entity:
                try:
                    user_id = user_entity.id
                    user_name = user_entity.username
                except Exception as e:
                    logging.debug('ex:%s' % str(e))
                    user_id = 1
                    user_name = 'System'
            else:
                user_id = 1
                user_name = 'System'

            actions = LabOrder.STATUS_CHOICES

            if action_value == '':
                action_value = action
                for sta in actions:
                    if sta[0] == action:
                        action_value = sta[1]

            return self.__tracking_extends(
                order_number,
                sku,
                order_date,
                lab_order_entity,
                user_id,
                user_name,
                action,
                action_value,
                remark
            )

        except Exception as e:
            logging.debug(str(e))
            rm.code = -1
            rm.capture_execption(e)

        return rm

    def get_order_history(self, entity):
        rm = response_message()
        try:
            lbo = None
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity)
            if not lbos == None:
                if len(lbos) > 0:
                    lbo = lbos[0]

            logging.debug(lbos)

            if not lbo == None:
                ots = OrderTracking.objects.filter(lab_order_entity=lbo.id).order_by('-id')
                rm.obj = ots

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def get_order_history_en(self, entity):
        rm = response_message()
        try:
            lbo = None
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity)
            if not lbos == None:
                if len(lbos) > 0:
                    lbo = lbos[0]

            logging.debug(lbos)

            if not lbo == None:

                sql = '''
                    select id,type,order_number,sku,order_date,remark,create_at,update_at,user_entity,username
                    ,lab_order_entity,action,action_value
                    ,case
                    when action='' then 'New job'
                    when action='REQUEST_NOTES' then 'Request for frame'
                    when action='FRAME_OUTBOUND' then 'Frame picked'
                    when action='PRINT_DATE' then 'Job printed'
                    when action='LENS_OUTBOUND' then 'Lens picked'
                    when action='LENS_REGISTRATION' then 'Lenses received'
                    when action='INITIAL_INSPECTION' then 'Lenses Inspection'
                    when action='LENS_RETURN' then 'Failed lens-inspection'
                    when action='LENS_RECEIVE' then 'Lens ready'
                    when action='ASSEMBLING' then 'Being Assembled'
                    when action='ASSEMBLED' then 'Glasses Assembled'
                    when action='GLASSES_RECEIVE' then 'Glasses Made'
                    when action='FINAL_INSPECTION' then 'QC In Progress'
                    when action='FINAL_INSPECTION_YES' then 'QC Passed'
                    when action='FINAL_INSPECTION_NO' then 'QC Failed'
                    when action='GLASSES_RETURN' then 'Glasses Rework'
                    when action='COLLECTION' then 'Shipment pairing'
                    when action='PRE_DELIVERY' then 'Prepare for shipping'
                    when action='PICKING' then 'Ready to ship'
                    when action='ORDER_MATCH' then 'Order Pairing'
                    when action='BOXING' then 'Shipment ready'
                    when action='SHIPPING' then 'Shipped from lab'
                    when action='DELIVERED' then 'Delivered'
                    when action='ONHOLD' then 'On hold'
                    when action='CANCELLED' then 'Cancelled'
                    when action='REDO' then 'Being remade'
                    when action='R2HOLD' then 'Request to hold'
                    when action='R2CANCEL' then 'Request to cancel'
                    when action='CLOSED' then 'Closed'
                    when action='COMPLETE' then 'Complete'
                    else action end as action_value_en
                    from oms_ordertracking
                    where lab_order_entity=%s
                    order by id desc;
                '''

                with connections["pg_oms_query"].cursor() as cursor:
                    sql = sql % lbo.id
                    cursor.execute(sql)
                    items = namedtuplefetchall(cursor)
                rm.obj = items

        except Exception as e:
            rm.capture_execption(e)

        return rm

    def post2mrp(self, ot):
        try:
            rm = response_message()
            rm.code = 0
            rm.message = ''
            # 推送到MRP
            logging.debug('开始推送到MRP')
            url = MRP_BASE_URL + 'api/JobTracking/'
            values = {}
            
            time.sleep(1)
            if ot.user_entity:
                user_entity_id = str(ot.user_entity)
            else:
                user_entity_id = "0"

            lab_order = LabOrder.objects.get(id=ot.lab_order_entity)
            order_number = lab_order.order_number

            values['user_id'] = user_entity_id
            values['user_name'] = ot.username
            values['comments'] = ot.remark
            values['order_number'] = order_number
            values['entity_id'] = ot.id
            values['entity_created_at'] = str(ot.create_at)
            values['lab_number'] = ot.order_number
            values['status'] = ot.action_value
            values['action'] = ot.action
            values['action_value'] = ot.action_value
            values['frame'] = ot.sku
            values['lens_sku'] = ot.sku

            headers = {'Content-Type': 'application/json'}
            data = json.dumps(values)  # 数据进行编码
            logging.debug('valus:%s' % data)
            req = requests.post(url=url, data=data, headers=headers)
            resp = req.text
            respjs = json.loads(resp)
            if respjs['code'] == 200:
                logging.debug(respjs['message'])
                ot.is_sync = 1
                ot.save()

        except Exception as ex:
            logging.critical(str(ex))


# OperationLog


class tracking_operation_controller:

    def tracking(
            self, type, entity, doc_number, action_value, field, user, origin_value, new_value,
            content=None,
            comments=None
    ):
        rm = response_message()
        try:
            opt_log = OperationLog()

            opt_log.object_type = type
            opt_log.object_entity = entity
            opt_log.doc_number = doc_number
            opt_log.action = action_value
            opt_log.fields = field

            user_id = -1
            user_name = 'System'
            try:
                user_id = user.id
                user_name = user.username
                opt_log.user_entity = user
            except Exception as e:
                logging.debug(str(e))

            opt_log.user_id = user_id

            opt_log.user_name = user_name
            opt_log.origin_value = origin_value
            opt_log.new_value = new_value
            opt_log.content = content
            opt_log.comments = comments
            opt_log.save()

            rm.code = 0
            rm.message = ''
        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)

        return rm

    def get_operation_history(self, type, entity):
        rm = response_message()
        try:
            ots = OperationLog.objects.filter(object_entity=entity, object_type=type)
            rm.obj = ots

        except Exception as e:
            rm.capture_execption(e)

        return rm
