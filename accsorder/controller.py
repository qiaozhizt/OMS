# -*- coding: utf-8 -*-

import logging

from util.db_helper import *
from util.response import *
from util.dict_helper import *
from util.format_helper import *
# from oms.models.order_models import LabOrder
import requests
import datetime

from util.response import response_message
#from wms.models import inventory_struct_warehouse
from .models import AccsOrder
from pg_oms.settings import BAR_CODE_PREFIX
from django.db import connections
from util.db_helper import namedtuplefetchall
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller
from pg_oms.settings import *


class AccsOrderController:
    """

    """

    def add(self, request, data):
        rm = response_message()
        user_id = 0
        user_name = "System"

        if request:
            user_id = request.user.id
            user_name = request.user.username

        if not data:
            rm.code = -2
            rm.message = "AccsOrder Data can't be null"
            return rm

        pg_order_item_entity = data.get('pg_order_item_entity', 0)
        if not pg_order_item_entity:
            rm.code = -2
            rm.message = "Pg Order Item Entity can't be null"
            return rm
        pg_order_item = data.get('pg_order_item', None)
        lab_number = pg_order_item.generate_lab_order_number()
        try:
            #pgborderitems = PgOrderItem.objects.filter(order_number=number).values_list(
            #    'attribute_set_name', flat=True)
            pg_sql = """SELECT attribute_set_name,lens_sku,so_type FROM oms_pgorderitem WHERE order_number='%s'""" % pg_order_item_entity.get('order_number')
            with connections['pg_oms_query'].cursor() as cursor:
                blue_glasses_sql = """SELECT frame FROM oms_blue_glasses WHERE is_enabled=TRUE"""
                cursor.execute(blue_glasses_sql)
                blue_glasses_list = [item.frame for item in namedtuplefetchall(cursor)]

                cursor.execute(pg_sql)
                pgborderitems = namedtuplefetchall(cursor)
                glasses_len = 0
                for item in pgborderitems:
                    #if (item.attribute_set_name == 'Glasses' and item.lens_sku not in blue_glasses_list) or \
                    #        item.attribute_set_name == 'Goggles' or item.so_type != 'frame_only':
                    if (item.attribute_set_name == 'Goggles' or (item.attribute_set_name == 'Glasses' and item.lens_sku not in blue_glasses_list)) and item.so_type != 'frame_only':
                        glasses_len = glasses_len + 1

                accs_comments = ''
                lab_comments = ''
                if len(pgborderitems) != glasses_len and glasses_len != 0:
                    is_rx_have = True
                    lab_comments = '具有LabOrders'
                    # sel_sql = """SELECT lab_number, frame, quantity, comments_ship FROM oms_laborder WHERE order_number='%s'""" % pg_order_item_entity.get('order_number')
                    # cursor.execute(sel_sql)
                    #
                    # laborders = namedtuplefetchall(cursor)
                    # for item in laborders:
                    #     lab_comments = lab_comments + "\t" + "具有LabOrders:{0}/{1}/{2}".format(item.lab_number, item.sku, item.quantity)
                    #
                    # if len(laborders) > 0:
                    #     laborder = laborders[0]
                    #     with connections['default'].cursor() as cursor2:
                    #         accs_comments = laborder.comments_ship + "\t" + "具有AccsOrders:{0}/{1}/{2}".format("AO" + data.get('lab_number'), pg_order_item_entity.get('frame'), pg_order_item_entity.get('quantity'))
                    #         update_sql = """UPDATE oms_laborder SET comments_ship='%s' WHERE order_number='%s'""" %(accs_comments, pg_order_item_entity.get('order_number'))
                    #         cursor2.execute(update_sql)
                    #         connections['default'].commit()
                else:
                    is_rx_have = False

                is_blue = False
                if pg_order_item_entity.get('lens_sku') in blue_glasses_list:
                    poc = pgorder_frame_controller()
                    res_rm = poc.get_lab_frame({"pg_frame": pg_order_item_entity.get('frame')})
                    lab_frame = res_rm.obj['lab_frame'] + 'U'
                    is_blue = True
                else:
                    if pg_order_item_entity.get('so_type') == 'frame_only':
                        lab_frame = pg_order_item_entity.get('frame')[1:]
                    else:
                        lab_frame = pg_order_item_entity.get('frame')

                ship_direction = pg_order_item_entity.get('ship_direction')
                sql = """SELECT * FROM wms_inventory_struct_warehouse WHERE sku='%s' AND warehouse_code='%s'""" % (
                lab_frame, 'US-AC01')
                cursor.execute(sql)
                invss = namedtuplefetchall(cursor)

                if ship_direction == 'STANDARD':
                    if len(invss) > 0:
                        quantity = invss[0].quantity
                        diff_quantity = quantity - pg_order_item_entity.get('quantity')
                        if diff_quantity > 0:
                            warehouse = 'US-AC01'
                        else:
                            if is_blue:
                                for i in range(0, pg_order_item.quantity):
                                    pg_order_item.generate_lab_order(index=i)
                                return True
                            else:
                                warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'
                    else:
                        if is_blue:
                            for i in range(0, pg_order_item.quantity):
                                pg_order_item.generate_lab_order(index=i)
                            return True
                        else:
                            warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'
                else:
                    if is_rx_have:
                        if is_blue:
                            for i in range(0, pg_order_item.quantity):
                                pg_order_item.generate_lab_order(index=i)
                            return True
                        else:
                            warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'
                    else:
                        if len(invss) > 0:
                            quantity = invss[0].quantity
                            diff_quantity = quantity - pg_order_item_entity.get('quantity')
                            if diff_quantity > 0:
                                warehouse = 'US-AC01'
                            else:
                                if is_blue:
                                    for i in range(0, pg_order_item.quantity):
                                        pg_order_item.generate_lab_order(index=i)
                                    return True
                                else:
                                    warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'
                        else:
                            if is_blue:
                                for i in range(0, pg_order_item.quantity):
                                    pg_order_item.generate_lab_order(index=i)
                                return True
                            else:
                                warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'

            sku = pg_order_item_entity.get('frame')
            name = ''
            with connections['pg_oms_query'].cursor() as cursor_p:
                psql = """SELECT * FROM wms_product_frame WHERE sku='%s'""" % sku
                cursor_p.execute(psql)
                p_product = namedtuplefetchall(cursor_p)
                if len(p_product) > 0:
                    product = p_product[0]
                    name = product.name

            ao = AccsOrder()
            ao.user_id = user_id
            ao.user_name = user_name
            ao.base_entity = pg_order_item_entity.get('id')
            ao.base_type = pg_order_item_entity.get('type')
            ao.accs_order_number = "AO" + lab_number#data.get('lab_number')
            ao.order_number = pg_order_item_entity.get('order_number')
            ao.sku = lab_frame #pg_order_item_entity.get('frame')
            ao.name = name
            ao.quantity = 1#pg_order_item_entity.get('quantity')
            ao.order_date = pg_order_item_entity.get('order_datetime')
            ao.is_rx_have = is_rx_have
            ao.warehouse = warehouse
            ao.comments = lab_comments
            ao.ship_direction = ship_direction
            ao.image = pg_order_item_entity.get('image')
            ao.thumbnail = pg_order_item_entity.get('thumbnail')
            ao.save()

            rm.obj = ao

        except Exception as ex:
            #rm.capture_execption(ex)
            sku = pg_order_item_entity.get('frame')
            is_blue = False
            with connections['pg_oms_query'].cursor() as cursor:
                blue_glasses_sql = """SELECT frame FROM oms_blue_glasses WHERE is_enabled=TRUE"""
                cursor.execute(blue_glasses_sql)
                blue_glasses_list = [item.frame for item in namedtuplefetchall(cursor)]

            if pg_order_item_entity.get('lens_sku') in blue_glasses_list:
                poc = pgorder_frame_controller()
                res_rm = poc.get_lab_frame({"pg_frame": pg_order_item_entity.get('frame')})
                lab_frame = res_rm.obj['lab_frame'] + 'U'
                is_blue = True
            else:
                if pg_order_item_entity.get('so_type') == 'frame_only':
                    lab_frame = pg_order_item_entity.get('frame')[1:]
                else:
                    lab_frame = pg_order_item_entity.get('frame')

            name = ''
            with connections['pg_oms_query'].cursor() as cursor_p:
                psql = """SELECT * FROM wms_product_frame WHERE sku='%s'""" % sku
                cursor_p.execute(psql)
                p_product = namedtuplefetchall(cursor_p)
                if len(p_product) > 0:
                    product = p_product[0]
                    name = product.name

            # if is_blue:
            #     pg_order_item.generate_lab_order()
            #     return True
            # else:
            ao = AccsOrder()
            ao.user_id = user_id
            ao.user_name = user_name
            ao.base_entity = pg_order_item_entity.get('id')
            ao.base_type = pg_order_item_entity.get('type')
            ao.accs_order_number = "AO" + lab_number#data.get('lab_number')
            ao.order_number = pg_order_item_entity.get('order_number')
            ao.sku = lab_frame #pg_order_item_entity.get('frame')
            ao.name = name
            ao.quantity = 1#pg_order_item_entity.get('quantity')
            ao.order_date = pg_order_item_entity.get('order_datetime')
            ao.is_rx_have = True
            ao.warehouse = self.check_warehous(pg_order_item_entity.get('so_type'))#'AC02'
            ao.comments = ''
            ao.ship_direction = pg_order_item_entity.get('ship_direction')
            ao.save()
            rm.obj = ao
        return rm

    def check_warehous(self, so_type):
        if so_type == 'frame_only':
            warehouse = 'W02'
        else:
            warehouse = 'AC02'

        return warehouse



def get_by_entity(entity):
    objs = []
    try:
        obj = None
        _entity = entity[0]
        if _entity.upper() == "A" and 'O' not in entity:
            _entity = entity.upper().lstrip("A")
            obj = AccsOrder.objects.get(id=_entity)
        else:
            if len(entity) <= 16 and len(entity) >= 4:
                objs = AccsOrder.objects.filter(accs_order_number__contains=entity).order_by('-id')
            else:
                obj = AccsOrder.objects.get(accs_order_number=entity)

        if not obj == None:
            objs.append(obj)

    except Exception as e:
        logging.debug(e.message)

    return objs


def get_by_entity_filter(entity):
    filter = {}
    try:
        _entity = entity[0]
        if _entity.upper() == "A" and 'O' not in entity:
            _entity = entity.upper().lstrip("A")
            filter['id'] = _entity
        else:
            if len(entity) <= 16 and len(entity) >= 4:
                filter['accs_order_number__contains'] = entity
            else:
                filter['accs_order_number'] = entity
    except Exception as e:
        logging.debug(e.message)

    return filter
