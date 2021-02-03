# -*- coding: utf-8 -*-

import logging

from api.json_response import JsonResponse
from oms.models.order_models import PgOrder, LabOrder, PgOrderItem, OrderActivity
from django.db import transaction
from util.response import response_message
from oms.models.application_models import OperationLog
from wms.models import inventory_struct_contoller
from api.controllers.tracking_controllers import tracking_lab_order_controller
from util.db_helper import DbHelper, namedtuplefetchall
from django.db import connections
from django.db.models import Q
import datetime


class pg_order_controller:
    '''
    PG Order Controller class
    # param: PG Order order_number
    '''

    def __init__(self, order_number = ''):
        if order_number:
            self.m_order_number = order_number
            self.pg_order = PgOrder.objects.get(order_number=order_number)
        elif order_number =='':
            self.m_order_number=order_number
            self.pg_order = None


    def cancel_order(self, content, reason, user, res_msg):
        '''取消PG Order并暂停对应所有Lab Order'''
        try:
            if not self.pg_order.is_inlab:
                pois = PgOrderItem.objects.filter(pg_order_entity=self.pg_order)
                isc = inventory_struct_contoller()
                for item in pois:
                    #frame = item.frame[1:8]
                    res_rm = self.get_lab_frame({"pg_frame": item.frame})
                    frame = res_rm.obj['lab_frame']
                    isc.subtract_reserver_qty(frame, item.quantity)

            with transaction.atomic():
                # 首先暂停PG Order所有对应的Lab Order
                stat_dict = ('CANCELLED', 'ONHOLD', 'SHIPPING')  # 不能暂停的状态
                lab_orders = self.get_lab_order()
                tloc = tracking_lab_order_controller()
                for lbo in lab_orders:
                    if lbo.status in stat_dict:
                        continue
                    lbo.current_status = lbo.status
                    lbo.status = 'ONHOLD'
                    lbo.save()
                    # 添加日志
                    tloc.tracking(lbo, user, 'ONHOLD', "暂停", reason)

                # 取消PG Order
                self.pg_order.status = 'canceled'
                self.pg_order.is_enabled = False
                self.pg_order.save()
                # 添加操作记录
                ol = OperationLog()
                ol.log(self.pg_order.type, self.pg_order.id, content, "status_v3", user)
                res_msg.obj = self.pg_order

        except Exception as e:
            res_msg.code = -1
            res_msg.exception = e
            res_msg.obj = self.pg_order
            return res_msg

        return res_msg

    def hold_order(self,pg_order_entity):
        '''暂停PG Order及对应所有Lab Order'''
        pass

    def get_lab_order(self):
        '''获取对应所有Lab Order'''
        return LabOrder.objects.filter(order_number=self.m_order_number)

    def set_ship_direction(self):
        '''设置PG Order及对应所有Lab Order发货方式'''
        pass

    def get_order_type(self, data_dict):
        try:
            lens_sku = data_dict.get('lens_sku', '')
            tint_name = data_dict.get('tint_name', '')
            sql = """SELECT is_rx_lab FROM oms_pgproduct WHERE sku='%s'""" % lens_sku
            with connections['pg_oms_query'].cursor() as conn:
                conn.execute(sql)
                results = namedtuplefetchall(conn)
                result = results[0]
                if tint_name != '' and tint_name is not None:
                    return 'TINT_LENS'
                elif result.is_rx_lab:
                    return 'RX_LENS'
                else:
                    return 'STOCK_LENS'

        except Exception as e:
            return ''

        finally:
            conn.close()

    def hold(self, request, entity_id, item_id, reason, ticketNumber=None, is_web='N'):
        """
        2019.09.29
        wy
        重写pgorder得hold操作接口
        :return:
        """
        """
        not in lab的pgorder 直接修改为hold状态，发出提示
        """
        rm = response_message()
        user_id=1
        user_name="System"
        pg_order =''
        if request:
            user_id = request.user.id
            user_name = request.user.username

        if entity_id == None or entity_id == '':
            rm.code = -1
            rm.message = "your entity_id is null"
            return rm

        if reason == None or reason == '':
            rm.code = -1
            rm.message = "your hold request reason is null"
            return rm


        pg_orders=PgOrder.objects.filter(base_entity=entity_id)
        if len(pg_orders) > 0:
            pg_order=pg_orders[0]
        if len(pg_orders) == 0:
            rm.code = -1
            rm.message = "your order not exist"
            return rm

        if pg_order.status in ('Hold Request ', 'holded', 'Hold Request', 'r2hold'):
            rm.code = -1
            rm.message = "Order is already holded"
            return rm

        if pg_order.status in ('closed', 'shipped', 'delivered'):
            rm.code = -1
            rm.message = "The order status is 'closed' or 'shipped' or 'delivered' cannot be R2Hold"
            return rm

        if ticketNumber == None:
            reason = reason
        else:
            reason = reason + " ticket_number:" + ticketNumber

        if is_web == 'N':
            User = request.user
        else:
            User = None

        if is_web == 'N':
            reason = "员工"+user_name+"操作："+reason
        else:
            reason = "客户操作："+reason

        oa = OrderActivity()
        tloc = tracking_lab_order_controller()
        try:
            logging.debug(pg_order.is_inlab)
            if pg_order.is_inlab:
                if item_id != '':
                    """
                    如果给定了item id，如果pg item只有一个，pg order 也暂停或申请暂停；
                    如果多余1个，只暂停一个item
                    """
                    pois = PgOrderItem.objects.filter(order_number=pg_order.order_number, item_id=item_id)
                    if len(pois) == 1:
                        pg_order.status = 'r2hold'
                        pg_order.save()

                    for item in pois:
                        if item.status in ['r2hold', 'holded']:
                            continue

                        item.status = 'r2hold'
                        item.save()
                        lab_info = LabOrder.objects.filter(lab_number=item.lab_order_number)
                        logging.debug(lab_info.query)
                        for lbo in lab_info:
                            if lbo.status in ['R2HOLD', 'HOLD', 'COMPLETE']:
                                rm.code = -1
                                rm.message = "LabOrder is already holded"
                                return rm

                            lbo.current_status = lbo.status
                            lbo.status = 'R2HOLD'
                            lbo.save()
                            # 写操作记录
                            tloc.tracking(lbo, User, "R2HOLD", "申请暂停", reason)
                else:
                    pois = PgOrderItem.objects.filter(order_number=pg_order.order_number)
                    for item in pois:
                        if item.status in ['r2hold', 'holded']:
                            continue

                        item.status = 'r2hold'
                        item.save()
                        lab_info = LabOrder.objects.filter(lab_number=item.lab_order_number)
                        for lbo in lab_info:
                            if lbo.status in ['R2HOLD', 'HOLD', 'COMPLETE']:
                                rm.code = -1
                                rm.message = "LabOrder is already holded"
                                return rm

                            lbo.current_status = lbo.status
                            lbo.status = 'R2HOLD'
                            lbo.save()
                            # 写操作记录
                            tloc.tracking(lbo, User, "R2HOLD", "申请暂停", reason)
                    pg_order.status = 'r2hold'
                    pg_order.save()

                rm.code = 0
                rm.message = "the order is in lab"
            else:
                pois = PgOrderItem.objects.filter(order_number=pg_order.order_number)
                for item in pois:
                    item.status = 'holded'
                    item.save()

                pg_order.status = 'holded'
                pg_order.save()

                rm.code = 0
                rm.message = "your order hold success"

            """
            # 记录hold reason ，写入order Activites
            # """
            oa.add_activity(pg_order.type, pg_order.id, pg_order.order_number, 'Hold Request',
                                        user_id, user_name, reason, 'h2hold')
            return rm
        except Exception as e:
            logging.debug(e.message)
            oa.add_activity(pg_order.type, pg_order.id, pg_order.order_number, 'Hold Request Fail',
                                        user_id, user_name, e, 'h2hold-fail')
            rm.code = -1
            rm.message = e
            return rm

    def get_lab_frame(self, data_dict):
        rm = response_message()
        try:
            rvalue = {}
            pg_frame = data_dict.get('pg_frame', '')
            category_id = pg_frame[0]
            lens_color = pg_frame[-1]
            if lens_color not in ['G', 'B', 'E']:
                lens_color = ''
                lab_frame = pg_frame[1:]
                sg_flag = False
            else:
                lab_frame = pg_frame[1:-1]
                sg_flag = True
            rvalue['category_id'] = category_id
            rvalue['lab_frame'] = lab_frame
            rvalue['sg_flag'] = sg_flag
            rvalue['lens_color'] = lens_color
            rm.obj = rvalue
            return rm
        except Exception as ex:
            rm.capture_execption(ex)
            return rm

    def refund(self, data):
        rm = response_message()

        try:
            order_number = data.get('order_number', 0)
            if not order_number:
                rm.code = -2
                rm.message = "Pg Order Not found!"
                return rm

            po = PgOrder.objects.get(order_number=order_number)

            if po.status not in ['processing', 'pending_csr', 'shipped', 'delivered']:
                rm.code = -3
                rm.message = "Pg Order status [%s] is not validate" % po.status
                return rm

            po.status = 'refund'
            po.save()

        except Exception as ex:
            rm.capture_execption(ex)

        return rm

    def set_priority(self, request, data):
        rm = response_message()
        try:
            user = {
                'id': 0,
                'username': 'System'
            }

            if request:
                user = request.user

            order_number = data.get('order_number', 0)
            priority = data.get('priority', 0)
            if not order_number:
                rm.code = -2
                rm.message = "Pg Order Not found!"
                return rm

            po = PgOrder.objects.get(order_number=order_number)

            if po.status in ['complete', 'shipped', 'delivered']:
                rm.code = -3
                rm.message = "Pg Order status [%s] is not validate" % po.status
                return rm

            PgOrder.objects.filter(order_number=order_number).update(priority=priority)
            PgOrderItem.objects.filter(order_number=order_number).update(priority=priority)
            LabOrder.objects.filter(order_number=order_number).update(priority=priority)

            logging.debug('changed priority ....')

            from api.controllers.tracking_controllers import tracking_operation_controller
            tc = tracking_operation_controller()
            tc.tracking(
                po.type, po.id,
                po.order_number,
                'set_priority',
                'priority',
                user,
                po.priority, priority,
                None,
                None,
            )

            logging.debug('logging operation ....')

        except Exception as ex:
            rm.capture_execption(ex)

        return rm

    def set_order2delivered(self, request, order_number, delivered_at=None):
        rm = response_message
        try:
            _delivered_at = datetime.datetime.now()
            if delivered_at:
                _delivered_at = delivered_at

            lbo_items = LabOrder.objects.filter(order_number=order_number).exclude(
                Q(status='R2CANCEL') |
                Q(status='CANCELLED') |
                Q(status='CLOSED')
            )

            is_all_delivered = True
            for item in lbo_items:
                if item.status != 'DELIVERED':
                    is_all_delivered = False

            if is_all_delivered:
                pgo = PgOrder.objects.get(order_number=order_number)
                if pgo.status == 'processing' or pgo.status == 'shipped':
                    PgOrder.objects.filter(order_number=order_number).update(
                        status='delivered',
                        delivered_at=_delivered_at
                    )
        except Exception as ex:
            rm.capture_execption(ex)

        return rm
