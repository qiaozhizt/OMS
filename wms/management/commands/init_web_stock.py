# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from wms.web_inventory import web_inventory
import logging
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical("***************初始化库存预留数量查询***************")
        try:
            logging.debug('start ....')
            wi = web_inventory()
            # wi.syns_base_stock()
            results=wi.init_reserve_qty()
        except Exception as e:
            logging.debug(e.message)

        logging.debug("**********初始库存结构预留库存数量结束***************")
