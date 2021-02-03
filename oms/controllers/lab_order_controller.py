# -*- coding: utf-8 -*-

import logging

from util.db_helper import *
from util.response import *
from util.dict_helper import *
from util.format_helper import *
import requests
import simplejson as json

from oms.models.order_models import *
from oms.models.response_models import *
from oms.models.exceptions_models import LabOrderStatusVerifyException
from pg_oms import settings

class lab_order_controller:
    def __init__(self, order_query=None, user=None):
        self.orders = order_query
        self.user = user

    def get_by_entity(self, entity):
        objs = []
        try:
            obj = None
            _entity = entity[0]
            if _entity.upper() == settings.BAR_CODE_PREFIX:
                _entity = entity.upper().lstrip(settings.BAR_CODE_PREFIX)
                obj = LabOrder.objects.get(id=_entity)
            elif _entity.upper() == 'R':
                try:
                    entity = entity[2:]
                    objs = LabOrder.objects.filter(vendor_order_reference__contains=entity)
                    obj = objs[0]
                except Exception as e:
                    obj = None
            else:
                if len(entity) <= 10 and len(entity) >= 4:
                    objs = LabOrder.objects.filter(lab_number__contains=entity).order_by('-id')
                else:
                    obj = LabOrder.objects.get(lab_number=entity)

            if not obj == None:
                objs.append(obj)

        except Exception as e:
            logging.debug(e.message)

        return objs

    def verify_status(self, entity):
        objs = self.get_by_entity(entity)
        if len(objs) == 1:
            obj = objs[0]
            if obj.status == '' \
                    or obj.status == 'SHIPPING' \
                    or obj.status == 'COMPLETE' \
                    or obj.status == 'ONHOLD' \
                    or obj.status == 'CANCELLED' \
                    or obj.status == 'R2HOLD' \
                    or obj.status == 'R2CANCEL' \
                    or obj.status == 'DELIVERED':
                raise LabOrderStatusVerifyException(obj.lab_number, obj.get_status_display())

            return True
        else:
            raise LabOrderStatusVerifyException(entity, entity)

    def hold_orders(self, tloc, reason):
        if not self.orders == None:
            for item in self.orders:
                item.current_status = item.status
                item.status = 'ONHOLD'
                item.save()
                # 添加日志
                tloc.tracking(item, self.user, 'ONHOLD', '暂停', reason)

    def post_mrp(self,lbo):
        rm = response_message()
        rm.code = 0
        rm.message = ''
        # 推送到MRP
        logging.debug('开始推送到MRP')
        url = MRP_BASE_URL + 'api/LabOrder/'
        values = {}
        values=dict_helper.convert_to_dict(lbo)

        entity_id = lbo.id

        headers = {'Content-Type': 'application/json'}
        data = json.dumps(values,cls=DateEncoder)  # 数据进行编码
        logging.debug('valus:%s' % data)
        req = requests.post(url=url, data=data, headers=headers)
        resp = req.text
        respjs = json.loads(resp)
        if respjs['code'] == 200:
            logging.debug(respjs['message'])
            obj = LabOrder.objects.get(id=entity_id).update(is_sync=True)
        else:
            logging.critical(respjs['data'])

    def cancel_lab_order(self, lbo):
        try:
            rm = response_message()
            with connections['default'].cursor() as cursor:
                update_sql ="""UPDATE oms_laborder SET `status`='%s' WHERE lab_number='%s'""" % ('CANCELLED', lbo.lab_number)
                cursor.execute(update_sql)
                lab_sql = """SELECT `status` FROM oms_laborder WHERE base_entity=%s""" % lbo.base_entity
                cursor.execute(lab_sql)
                laborders = namedtuplefetchall(cursor)
                counts = str(laborders).count("CANCELLED")
                if len(laborders) == counts:
                    is_invalid = True
                else:
                    is_invalid = False

                if is_invalid:
                    poi = PgOrderItem.objects.get(pk=lbo.base_entity)
                    # 取消对应PgOrderItem
                    poi.status = 'canceled'
                    poi.save()

                    pgorderitem_sql = """SELECT `status` FROM oms_pgorderitem WHERE order_number=%s""" % poi.order_number
                    cursor.execute(pgorderitem_sql)
                    pgorderitems = namedtuplefetchall(cursor)
                    pgorderitems_counts = str(pgorderitems).count("canceled")
                    if len(pgorderitems) == pgorderitems_counts:
                        do_cancel = True
                    else:
                        do_cancel = False

                    if do_cancel:
                        pg_order = poi.pg_order_entity
                        pg_order.status = 'canceled'
                        pg_order.save()
            rm.code = 0
            rm.message = '执行成功！'
            return rm
        except Exception as e:
            rm.code = -1
            rm.message = str(e)
            return rm
        finally:
            cursor.close()

    def get_tracking_code(self,lab_number):
        url = settings.SHIP_ROOT_URL + '/api/get_tracking_code/'
        api_response = requests.get(url, params={"lab_number": lab_number},
                                    headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        return response
