# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from oms.models.order_models import LabOrder
from django.db import connections
from util.db_helper import *
import logging
import datetime

class Command(BaseCommand):
    def handle(self,*args, **options):
        sql="SELECT id,frame,image,thumbnail FROM `oms_laborder` WHERE create_at > DATE_SUB(NOW(), INTERVAL 30 DAY) AND (image IS NULL or image='' OR thumbnail IS NULL or thumbnail='')"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)

        for prod in results:
            sql="select entity_id,image,thumbnail from catalog_product_flat_1 where stock_sku='{0}' and image is not null and image!='' and thumbnail is not null and thumbnail!='' limit 1"
            sql=sql.format(prod.frame)
            with connections['pg_mg_query'].cursor() as cursor:
                cursor.execute(sql)
                images=namedtuplefetchall(cursor)
            if images.__len__()==1:
                image=images[0]
                sql="update oms_laborder set image='{0}',thumbnail='{1}' where id={2}"
                sql=sql.format(image.image,image.thumbnail,prod.id)
                print(sql)
                connections['default'].cursor().execute(sql)
