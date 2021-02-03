# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# # Create your models here.
import logging
from time import strftime
from django.db import connections
from django.db import transaction

from util.base_type import base_type
from util.response import response_message
from util.db_helper import *


class api_request_log(models.Model):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OARL', editable=False)


class ProductParent(base_type):
    class Meta:
        db_table = 'merchandising_product_parent'

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OPRP', editable=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    category_id = models.IntegerField(u'Category ID', default=0)
    product_id = models.IntegerField(u'Product ID', default=0)
    category_name = models.CharField(u'Category Name', max_length=128, default='', blank=True, null=True)
    sku = models.CharField(u'SKU', max_length=128, default='', blank=True, null=True)
    name = models.CharField(u'Name', max_length=128, default='', blank=True, null=True)
    position = models.IntegerField(u'Position', default=0)
    is_in_stock = models.BooleanField(u'Is InStock', default=True)
    entity_created_at = models.CharField(u'Entity Created At', max_length=128, default='', blank=True, null=True)
    entity_updated_at = models.CharField(u'Entity Updated At', max_length=128, default='', blank=True, null=True)
    request_path = models.CharField(u'Request Path', max_length=128, default='', blank=True, null=True)
    price = models.CharField(u'Price', max_length=128, default='', blank=True, null=True)


class Product(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OPRD', editable=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    parent_id = models.IntegerField(u'Parent ID', default=0)
    category_id = models.IntegerField(u'Category ID', default=0)
    category_name = models.CharField(u'Category Name', max_length=128, default='', blank=True, null=True)
    product_id = models.IntegerField(u'Product ID', default=0)
    sku = models.CharField(u'SKU', max_length=128, default='', blank=True, null=True)
    frame_sku = models.CharField(u'Frame SKU', max_length=128, default='', blank=True, null=True)
    name = models.CharField(u'Name', max_length=128, default='', blank=True, null=True)
    image_url = models.CharField(u'Image URL', max_length=128, default='', blank=True, null=True)
    shape = models.CharField(u'Shape', max_length=128, default='', blank=True, null=True)
    material = models.CharField(u'Material', max_length=128, default='', blank=True, null=True)
    bridge = models.CharField(u'Bridge', max_length=128, default='', blank=True, null=True)
    temple_length = models.CharField(u'Temple length', max_length=128, default='', blank=True, null=True)
    width = models.CharField(u'Width', max_length=128, default='', blank=True, null=True)
    weight = models.CharField(u'Weight', max_length=128, default='', blank=True, null=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    position = models.IntegerField(u'Position', default=0)
    is_in_stock = models.BooleanField(u'Is InStock', default=True)
    request_path = models.CharField(u'Request Path', max_length=128, default='', blank=True, null=True)
    price = models.CharField(u'Price', max_length=128, default='', blank=True, null=True)


class ProductListController:
    sql_product_parent = """
            /* 查询所有产品在网站的排序 */
            SELECT t0.entity_id AS category_id
            ,t0.name AS category_name
            ,t2.entity_id AS product_id
            ,t2.sku
            ,t3.name
            ,t3.stock_sku
            ,t3.price
            ,RIGHT(t2.sku,LENGTH(t2.sku)-1) AS lab_sku
            /*,t2.name as product_name*/
            ,t1.position
            ,t5.request_path
            ,t4.is_in_stock
            ,t2.created_at AS entity_created_at
            ,t2.updated_at AS entity_updated_at
            FROM catalog_category_flat_store_1 t0
            LEFT JOIN catalog_category_product t1
            ON t0.entity_id=t1.category_id
            LEFT JOIN catalog_product_entity t2 
            ON t2.entity_id=t1.product_id
            LEFT JOIN catalog_product_flat_1 t3
            ON t2.entity_id=t3.entity_id
            LEFT JOIN cataloginventory_stock_item t4
            ON t4.item_id=t2.entity_id
            LEFT JOIN url_rewrite t5
            ON t5.entity_id=t1.entity_id
            WHERE 1=1
            -- t0.entity_id=6
            AND t2.type_id='configurable'
            -- AND t4.is_in_stock=1
            ORDER BY t0.entity_id,t1.position
    """

    sql_product = """
            /*
              查询所有产品的数据清单
            */
            SELECT 
            t4.parent_id
            ,t0.name
            ,t0.entity_id AS product_id
            ,t0.sku
            ,t0.stock_sku AS frame_sku
            ,CONCAT('https://static.payneglasses.com/media/catalog/product',t0.image) AS image
            ,t0.image AS image_url
            ,t0.frame_shape_value AS shape
            ,t0.material_value AS material
            ,t0.simeple_material_value AS detailed_material
            ,t0.bridge_value AS bridge
            ,t0.temple_length_value AS temple_length
            ,t0.frame_width_value AS width
            ,t0.frame_weight_value AS weight
            ,t0.price
            ,t3.category_id
            ,CAST((SELECT POSITION FROM catalog_category_product WHERE product_id=(SELECT parent_id FROM catalog_product_relation WHERE child_id=t0.entity_id LIMIT 1) LIMIT 1) AS SIGNED INTEGER) AS POSITION
            ,t1.qty AS quantity
            ,t2.stock_status
            ,t1.is_in_stock
            
            FROM catalog_product_flat_1 t0
            LEFT JOIN cataloginventory_stock_item t1
            ON t0.entity_id=t1.product_id
            LEFT JOIN cataloginventory_stock_status t2
            ON t0.entity_id=t2.product_id
            LEFT JOIN catalog_category_product t3
            ON t0.entity_id=t3.product_id
            LEFT JOIN catalog_product_relation t4
            ON t4.child_id = t0.entity_id
            WHERE t4.parent_id=%s
            -- t0.attribute_set_id=13
            -- AND t1.is_in_stock=1
            -- AND t0.type_id='simple'
            -- AND t3.category_id=6
            -- GROUP BY t0.sku
            -- ORDER BY t0.sku
    """

    base_url = "https://static.payneglasses.com/media/catalog/product"
    product_url = "https://www.payneglasses.com/"

    def GenerateAll(self):
        rm = response_message()

        sql = self.sql_product_parent
        items = []
        try:
            ProductParent.objects.all().delete()

            with connections['magentodb'].cursor() as cursor:
                cursor.execute(sql)
                items = dictfetchall(cursor)
                logging.critical("got data ....")
                count = len(items)
                logging.critical("count: %s" % count)

                for idx in range(count):
                    pp = ProductParent()
                    pp.__dict__.update(**items[idx])
                    if not pp.is_in_stock:
                        pp.is_in_stock = False
                    pp.save()

                    logging.critical("index[ %s ] product id: %s" % (idx, pp.product_id))

        except Exception as ex:
            logging.critical("exception as ProductParent: %s" % str(ex))
        finally:
            connections['magentodb'].close()

        pps = ProductParent.objects.all().order_by('id')
        Product.objects.all().delete()
        for pp in pps:
            logging.critical("Now pp product id is : %s" % pp.product_id)
            sql = self.sql_product % pp.product_id
            try:
                with connections['magentodb'].cursor() as cursor:
                    cursor.execute(sql)
                    items = dictfetchall(cursor)
                    logging.critical("got data detailed ....")
                    count = len(items)
                    logging.critical("count : %s" % count)
                    for idx in range(count):
                        try:
                            prod = Product()
                            prod.__dict__.update(**items[idx])
                            prod.category_id = pp.category_id
                            prod.category_name = pp.category_name
                            prod.position = pp.position
                            prod.request_path = pp.request_path
                            if not prod.quantity:
                                prod.quantity = 0

                            prod.save()
                        except Exception as e:
                            logging.critical('creating : %s' % str(e))

            except Exception as ex:
                logging.critical("exception as product: %s" % str(ex))
            finally:
                connections['magentodb'].close()

        return rm

    def GetAll(self, category_id=6, frame='', min_qty='', max_qty='', cate_type=''):
        rm = response_message()
        sql = """
            /*
              查询所有产品的数据清单
            */
            SELECT 
            t0.name
            ,t0.entity_id AS product_id
            ,t0.sku
            ,t0.stock_sku AS frame_sku
            ,CONCAT('https://static.payneglasses.com/media/catalog/product',t0.image) AS image
            ,t0.frame_shape_value AS frame_shape
            ,t0.material_value AS material
            ,t0.simeple_material_value AS detailed_material
            ,t0.bridge_value AS bridge
            ,t0.temple_length_value AS temple_length
            ,t0.frame_width_value AS frame_width
            ,t0.frame_weight_value AS frame_weight
            ,t3.category_id
            ,CAST((SELECT POSITION FROM catalog_category_product WHERE product_id=(SELECT parent_id FROM catalog_product_relation WHERE child_id=t0.entity_id LIMIT 1) LIMIT 1) AS SIGNED INTEGER) AS POSITION
            ,t1.qty
            ,t2.stock_status
            ,t1.is_in_stock
            
            FROM catalog_product_flat_1 t0
            LEFT JOIN cataloginventory_stock_item t1
            ON t0.entity_id=t1.product_id
            LEFT JOIN cataloginventory_stock_status t2
            ON t0.entity_id=t2.product_id
            LEFT JOIN catalog_category_product t3
            ON t0.entity_id=t3.product_id
            WHERE t0.attribute_set_id=13
            AND t1.is_in_stock=1
            AND t0.type_id='simple'
            AND t3.category_id=6
            GROUP BY t0.sku
            ORDER BY POSITION,t0.sku
        """

        sql_count = """
            SELECT parent_id,COUNT(id) AS skus FROM merchandising_product  WHERE 1=1 
            AND category_id=%s
        """
        if frame != '':
            sql_count = sql_count + """ AND sku like '%%%s%%'"""

        if cate_type == 'quantity':
            if min_qty != '' and max_qty != '':
                sql_count = sql_count + """  AND quantity BETWEEN %s AND %s"""
        elif cate_type == 'price':
            if min_qty != '' and max_qty != '':
                sql_count = sql_count + """  AND price BETWEEN %s AND %s"""

        sql_count = sql_count + """ GROUP BY parent_id """

        if frame != '':
            sql_count = sql_count % (category_id, frame)
        elif min_qty != '' and max_qty !='':
            sql_count = sql_count % (category_id, int(min_qty), int(max_qty))
        else:
            sql_count = sql_count % category_id


        try:
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql_count)
                items = namedtuplefetchall(cursor)
                rm.count = len(items)
        except Exception as ex:
            pass
        finally:
            connections['pg_oms_query'].close()

        sql = """
            SELECT 
            *
            FROM 
            merchandising_product
            WHERE 1=1 
            AND category_id=%s
        """
        if frame != '':
            sql = sql + """ AND sku like '%%%s%%'"""

        if cate_type == 'quantity':
            if min_qty != '' and max_qty != '':
                sql = sql + """  AND quantity BETWEEN %s AND %s"""
        elif cate_type == 'price':
            if min_qty != '' and max_qty != '':
                sql = sql + """  AND price BETWEEN %s AND %s"""

        sql = sql + """ GROUP BY sku ORDER BY id"""

        if frame != '':
            sql = sql % (category_id, frame)
        elif min_qty != '' and max_qty !='':
            sql = sql % (category_id, int(min_qty), int(max_qty))
        else:
            sql = sql % category_id


        try:
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                items = namedtuplefetchall(cursor)
                rm.obj = items
        except Exception as ex:
            pass
        finally:
            connections['pg_oms_query'].close()

        return rm
#
# class base_type(models.Model):
#     class Meta:
#         abstract = True
#
#     # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
#     type = models.CharField(u'类型', max_length=20, default='BAMO', editable=False)
#
#     # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
#     sequence = models.IntegerField(u'SEQUENCE', default=0)
#     is_enabled = models.BooleanField(u'IS Enabled', default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
#     user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
#     comments = models.CharField(u'Comments', max_length=4096, default='', blank=True, null=True)
#
#
# class comment(base_type):
#     # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
#     type = models.CharField(u'类型', max_length=20, default='PGCO', editable=False)
#
#     BIZ_TYPE_CHOICES = (
#         ('OPOR', 'Pg Order'),
#         ('PORL', 'Pg Order Item'),
#         ('OLOR', 'Lab Order'),
#     )
#
#     STATUS_CHOICES = (
#         ('0', 'New'),
#         ('1', 'Processing'),
#         ('2', 'Done'),
#         ('3', 'Closed'),
#     )
#
#     parent_entity = models.ForeignKey('self', models.CASCADE,
#                                       blank=True,
#                                       null=True, )
#
#     biz_type = models.CharField(u'Biz Type', max_length=20, default='', choices=BIZ_TYPE_CHOICES, null=True,
#                                 blank=True, )
#     biz_id = models.CharField(u'Biz ID', max_length=128, default='', null=True, blank=True, )
#
#     comments = models.TextField(u'Comments', default='', blank=True, null=True)
#
#     status = models.CharField(u'Status', max_length=20, default='0', choices=STATUS_CHOICES, null=True, blank=True, )
#
#     user_name = models.CharField(u'Reporter', max_length=128, default='', blank=True, null=True)
#     assign_id = models.CharField(u'Assign ID', max_length=128, default='', blank=True, null=True)
#     assign_name = models.CharField(u'Assign', max_length=128, default='', blank=True, null=True)
#
#     @property
#     def reviewed(self):
#         try:
#             objs = comment.objects.filter(parent_entity=self)
#             return len(objs)
#         except:
#             return 0
