# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.http import HttpRequest
from oms.controllers.order_controller import *


class Command(BaseCommand):
    def handle(self, *args, **options):

        logging.debug("Preparing PgOrder & Items maitance ....")

        with connections['pg_mg_query'].cursor() as cursor:
            sql = '''
            select order_id,item_id,profile_id,profile_prescription_id from sales_order_item where parent_item_id is null order by item_id
            '''

            cursor.execute(sql)

            results = namedtuplefetchall(cursor)

            if results:

                try:
                    with transaction.atomic():
                        for i in range(len(results)):
                            poi = PgOrderItem.objects.get(pg_order_entity__base_entity=results[i].order_id,
                                                          item_id=results[i].item_id)
                            poi.profile_id = results[i].profile_id
                            poi.profile_prescription_id = results[i].profile_prescription_id
                            poi.save()

                            logging.debug('Now poi[%s]' % poi.order_number)
                            logging.debug('[%s]' % poi.profile_id)


                except Exception as e:
                    logging.debug("When maintance order arise Errors: %s" % e)
            else:
                logging.debug("There is no PgOrders should be maintanced !")
