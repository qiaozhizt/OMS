# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

SQL_CATEGORY_PRODUCTS_INDEX = """
            /* 查询所有产品在网站的排序 */
            select t0.entity_id
            ,t0.name as category_name
            ,t2.entity_id as product_id
            ,t2.sku
            ,t3.name
            ,RIGHT(t2.sku,LENGTH(t2.sku)-1) as lab_sku
            /*,t2.name as product_name*/
            ,t1.position
            ,t2.created_at
            ,t2.updated_at
            
            from catalog_category_flat_store_1 t0
            left join catalog_category_product t1
            on t0.entity_id=t1.category_id
            left join catalog_product_entity t2 
            on t2.entity_id=t1.product_id
            left join catalog_product_flat_1 t3
            on t2.entity_id=t3.entity_id
            
            where t0.entity_id=%s
            and t2.type_id='configurable'
            order by t0.entity_id,t1.position
                """


# table_name :  表名字符串
# field_list :  查询字段字符串列表
# condition  :  筛选条件字符串列表
# group_by   :  按此字段分组
# order_by   :  按此字段排序
# join       :  联查 字符串列表
class simple_general_query:
    def __init__(self, table_name, field_list=['*'], condition=[], group_by='', order_by='', join=[]):
        self.m_table_name = table_name
        self.m_field_list = field_list
        self.m_join = join
        self.m_condition = condition
        self.m_group_by = group_by
        self.m_order_by = order_by
        self.m_sql = ''

    def check_sql(self):
        condition = ''
        group_up = ''
        order_by = ''
        if self.m_table_name == '':
            return -1
        if not len(self.m_condition) == 0:
            condition = "WHERE %s" % " AND ".join(self.m_condition)
        if not self.m_group_by == '':
            group_up = "GROUP BY %s" % self.m_group_by
        if not self.m_order_by == '':
            order_by = "ORDER BY %s DESC" % self.m_order_by

        self.m_sql = "SELECT %s FROM %s %s %s %s %s" % (
            ",".join(self.m_field_list),
            self.m_table_name,
            " ".join(self.m_join),
            condition,
            group_up,
            order_by
        )
        return self.m_sql
