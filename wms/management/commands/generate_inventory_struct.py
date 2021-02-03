# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.db.models import Q

from django.http import HttpRequest
from django.db import connections
from django.db import transaction

from wms.models import inventory_struct


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')

        index = 0

        try:
            logging.debug('start ....')

            sql = '''
            select  
                product_flat.entity_id,
                product_flat.sku,
                product_flat.name,
                item_stock.item_id,
                item_stock.product_id,
                item_stock.qty,
                item_stock.min_qty,
                item_stock.is_in_stock,
                product_entity.attribute_set_id,
                product_entity.type_id,
                product_entity.has_options,
                product_entity.required_options,
                product_entity.created_at,
                product_entity.updated_at 
                
                from catalog_product_flat_1 product_flat
                left join catalog_product_entity product_entity on product_flat.entity_id=product_entity.entity_id 
                left join cataloginventory_stock_item item_stock on item_stock.product_id=product_entity.entity_id 
                where item_stock.product_id=(select entity_id from catalog_product_entity where sku=%s);
            '''

            invs = inventory_struct.objects.all()
            for inv in invs:
                logging.critical(inv.sku)

                is_checked_stock_status = False

                women_sku = '1' + inv.sku
                men_sku = '2' + inv.sku
                kids_sku = '3' + inv.sku

                # women
                with connections['pg_mg_query'].cursor() as cursor:
                    cursor.execute(sql, [women_sku])
                    results = namedtuplefetchall(cursor)
                    if len(results) > 0:
                        inv.web_women_quantity = results[0].qty
                        inv.web_women_is_in_stock = results[0].is_in_stock
                        if inv.web_women_is_in_stock:
                            is_checked_stock_status = True
                            inv.status = 'IN_STOCK'
                        inv.name = results[0].name
                        inv.save()

                # men
                with connections['pg_mg_query'].cursor() as cursor:
                    cursor.execute(sql, [men_sku])
                    results = namedtuplefetchall(cursor)
                    if len(results) > 0:
                        inv.web_men_quantity = results[0].qty
                        inv.web_men_is_in_stock = results[0].is_in_stock
                        inv.status = 'IN_STOCK'
                        if not is_checked_stock_status and inv.web_men_is_in_stock:
                            inv.name = results[0].name
                            is_checked_stock_status = True
                        inv.save()

                # kids
                with connections['pg_mg_query'].cursor() as cursor:
                    cursor.execute(sql, [kids_sku])
                    results = namedtuplefetchall(cursor)
                    if len(results) > 0:
                        inv.web_kids_quantity = results[0].qty
                        inv.web_kids_is_in_stock = results[0].is_in_stock
                        if inv.web_kids_is_in_stock:
                            inv.status = 'IN_STOCK'
                            is_checked_stock_status = True
                        if not is_checked_stock_status:
                            inv.name = results[0].name
                        inv.save()

                if not is_checked_stock_status and (inv.name == '' or inv.name == None):
                    inv.status = 'DRAFT'
                    inv.save()
                elif not is_checked_stock_status:
                    inv.status = 'OUT_OF_STOCK'
                    inv.save()


        except Exception as e:
            logging.critical(e.message)

        logging.critical('generate lab orders completed ....')
