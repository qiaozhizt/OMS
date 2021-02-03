# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connections
from django.db import transaction

import logging
import simplejson as json

from order_models import *


class ResponseBody:
    def __init__(self,
                 code=0,
                 message=None,
                 exception=None,
                 object=None,
                 comments=None
                 ):
        self.code = code
        self.message = message
        self.exception = exception
        self.object = object
        self.comments = comments


class shipment:
    def __init__(self,
                 order_id,
                 entity_id=None,
                 billing_address_id=None,
                 shipping_address_id=None,
                 customer_id=None,
                 shipping_method='standard',
                 address=None,
                 glasses=None,
                 accessories=[]
                 ):
        self.order_id = order_id
        self.entity_id = entity_id
        self.shipping_method = shipping_method
        self.billing_address_id = billing_address_id
        self.shipping_address_id = shipping_address_id
        self.customer_id = customer_id
        self.address = address
        self.glasses = glasses
        self.accessories = accessories

    def post_shipment(self
                      ):
        with connections['pg_mg_query'].cursor() as cursor:
            sql = '''SELECT 
                t0.increment_id,
                t3.firstname,
                t3.lastname,
                t3.postcode,
                t3.street,
                t3.city,
                t3.region_id,
                t4.code AS region,
                t3.region AS region_name,
                t3.country_id,
                t3.telephone,
                t5.instruction
            FROM
                sales_order_grid t0
                    LEFT JOIN
                sales_order_address t3 ON t0.entity_id = t3.parent_id
                    AND t3.address_type = 'shipping'
                    LEFT JOIN
                directory_country_region t4 ON t4.region_id = t3.region_id
                    LEFT JOIN
                sales_order_additional t5 ON t0.entity_id = t5.order_entity
            WHERE
                t0.increment_id = %s'''

            logging.info(sql)
            logging.debug("---------------------------------------" + str(self.order_id))
            cursor.execute(sql, [self.order_id])
            results = self.dictfetchall(cursor)

            # logging.debug(results)
            # logging.debug(results[0]['firstname'])

            # 2019.12.25 by guof. OMS-544

            shipAddress = address()
            shipAddress.name = results[0]['firstname'] + " " + results[0]['lastname']

            # magneto地址是换行符分隔stree ranhy
            str_street = results[0]['street']
            str_street = str_street.encode('utf-8')
            sec_str = '\n'
            arr_street = str_street.split(sec_str)
            shipAddress.street1 = arr_street[0]
            if len(arr_street) > 1:
                shipAddress.street2 = arr_street[1]

            shipAddress.city = results[0]['city']
            shipAddress.state = results[0]['region']
            shipAddress.zip = results[0]['postcode']
            shipAddress.country = results[0]['country_id']
            shipAddress.phone = results[0]['telephone']

            glassesList = []

            # from .order_models import PgOrder
            # po = PgOrder.objects.get(order_number=self.order_id)

            # po.is_shiped_api = True
            # po.save()
            # from .order_models import PgOrderItem
            queryset = PgOrderItem.objects.select_related("lab_order_entity").filter(order_number=self.order_id)

            for pgorderitem in queryset:

                if pgorderitem.lab_order_number == None or pgorderitem.lab_order_number == '':
                    continue

                shipGlasses = glasses()
                lbo = LabOrder.objects.get(lab_number=pgorderitem.lab_order_number)
                shipGlasses.lab_order_entity = lbo.id
                shipGlasses.lab_order_id = pgorderitem.lab_order_number
                shipGlasses.frame_sku = pgorderitem.frame
                shipGlasses.item_id = pgorderitem.item_id
                shipGlasses.product_id = pgorderitem.product_id
                glassesList.append(shipGlasses.__dict__)

                # sendShipment = shipment()
            self.order_id = self.order_id
            self.entity_id = queryset[0].pg_order_entity.base_entity
            self.customer_id = queryset[0].pg_order_entity.customer_id
            self.billing_address_id = queryset[0].pg_order_entity.billing_address_id
            self.shipping_address_id = queryset[0].pg_order_entity.shipping_address_id
            self.shipping_method = queryset[0].get_ship_direction_display()
            self.address = shipAddress.__dict__
            self.glasses = glassesList

            return json.dumps(self.__dict__)

    def dictfetchall(self,
                     cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


class address:
    def __init__(self,
                 name='',
                 street1='',
                 street2='',
                 city='',
                 state='',
                 zip='',
                 country='US',
                 phone=''
                 ):
        self.name = name
        self.street1 = street1
        self.street2 = street2
        self.city = city
        self.state = state
        self.zip = zip
        self.country = country
        self.phone = phone


class glasses:
    def __init__(self,
                 lab_order_entity=0,
                 lab_order_id='',
                 frame_sku='',
                 color='',
                 item_id=None,
                 product_id=None,
                 accessories=[]
                 ):
        self.lab_order_entity = lab_order_entity
        self.lab_order_id = lab_order_id
        self.frame_sku = frame_sku
        self.color = color
        self.item_id = item_id
        self.product_id = product_id
        self.accessories = accessories


class Items:
    left = None
    right = None
    index = 1
    location = ''
    obj = None
    quantity = 0
    warehouse_code = ''


class ParentItems:
    count = 0
    index = 1
    items = None
    created_at = ''
    warehouse_code = ''
