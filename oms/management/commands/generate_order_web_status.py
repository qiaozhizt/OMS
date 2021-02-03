# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
import logging

from oms.views import *
from oms.const import *

from oms.controllers.order_controller import *


class Command(BaseCommand):
    def handle(self, *args, **options):

        logging.debug('Start ....')

        with connections['pg_mg_query'].cursor() as cursor:
            sql = const.sql_generate_pg_orders + const.sql_generate_pg_orders_all
            logging.info(sql)
            try:
                cursor.execute(sql, [7527])
                results = namedtuplefetchall(cursor)
                result = results[0]

                for result in results:

                    po = PgOrder.objects.get(order_number=result.increment_id)

                    # if not po.web_updated_at == result.updated_at:
                    logging.debug('----------------------------------------')
                    logging.debug('status: %s'%result.status)
                    po.web_status = result.status
                    po.save()

            except Exception as e:
                logging.debug("When generating order arise Errors: %s" % e)