# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging
from pg_oms import settings

"""MgOrder查询语句"""
MgSqlEqu = """select t0.entity_id       
            ,t0.increment_id
            ,(case when (t9.base_subtotal+t9.base_discount_amount>=50) then 1 else 0 end) as is_vip
            ,t0.status
            ,t0.created_at
            ,t0.updated_at
            ,(case when t0.payment_method='braintree' then 'credit_card' else t0.payment_method end) as payment_method
            ,(select convert(t9.total_qty_ordered,decimal)) as quantity
            ,(select FORMAT(t0.grand_total,2)) as grand_total
            ,CONCAT(t8.firstname,' ',t8.lastname) as customer_name
            ,(case when t9.shipping_method='standard_standard' then 'standard' when t9.shipping_method='express_express' then 'express' when t9.shipping_method='canada_express_canada_express' then 'ca_express' else t9.shipping_method end ) as shipping_method
            #,t8.email as cusomer_email
        from sales_order_grid t0
        left join customer_grid_flat t1
        on t1.entity_id = t0.customer_id
        left join sales_order t9
        on t9.entity_id = t0.entity_id
        left join customer_entity t8
        on t0.customer_id=t8.entity_id
        where t0.increment_id = %s
        order by t0.entity_id DESC """

MgSqlLike = """select t0.entity_id       
            ,t0.increment_id
            ,(case when (t9.base_subtotal+t9.base_discount_amount>=50) then 1 else 0 end) as is_vip
            ,t0.status
            ,t0.created_at
            ,t0.updated_at
            ,(case when t0.payment_method='braintree' then 'credit_card' else t0.payment_method end) as payment_method
            ,(select convert(t9.total_qty_ordered,decimal)) as quantity
            ,(select FORMAT(t0.grand_total,2)) as grand_total
            ,CONCAT(t8.firstname,' ',t8.lastname) as customer_name
            ,(case when t9.shipping_method='standard_standard' then 'standard' when t9.shipping_method='express_express' then 'express' when t9.shipping_method='canada_express_canada_express' then 'ca_express' else t9.shipping_method end ) as shipping_method
            #,t1.email as cusomer_email
        from sales_order_grid t0
        left join customer_grid_flat t1
        on t1.entity_id = t0.customer_id
        left join sales_order t9
        on t9.entity_id = t0.entity_id
        left join customer_entity t8
        on t0.customer_id=t8.entity_id
        where t0.increment_id like %s
        order by t0.entity_id DESC """

MgSqlEquName = """select t0.entity_id       
            ,t0.increment_id
            ,(case when (t9.base_subtotal+t9.base_discount_amount>=50) then 1 else 0 end) as is_vip
            ,t0.status
            ,t0.created_at
            ,t0.updated_at
            ,(case when t0.payment_method='braintree' then 'credit_card' else t0.payment_method end) as payment_method
            ,(select convert(t9.total_qty_ordered,decimal)) as quantity
            ,(select FORMAT(t0.grand_total,2)) as grand_total
            ,CONCAT(t8.firstname,' ',t8.lastname) as customer_name
            ,(case when t9.shipping_method='standard_standard' then 'standard' when t9.shipping_method='express_express' then 'express' when t9.shipping_method='canada_express_canada_express' then 'ca_express' else t9.shipping_method end ) as shipping_method
            #,t1.email as cusomer_email
        from sales_order_grid t0
        left join customer_grid_flat t1
        on t1.entity_id = t0.customer_id
        left join sales_order t9
        on t9.entity_id = t0.entity_id
        left join customer_entity t8
        on t0.customer_id=t8.entity_id
        where t1.name = %s
        order by t0.entity_id DESC """

# 2018.05.07 created by guof.
# 生成Pg Orders，都使用该SQL Script.

# magento 网站复合棱镜功能上线后需要更改
# 2019.12.17 by guof.
# origin order entity & order number
sql_generate_pg_orders = '''
        select t0.entity_id,t0.status,t0.increment_id
        ,t9.is_clone,t9.clone_order_id,t9.clone_order_number
        ,t0.shipping_name,t0.billing_name,t0.created_at
                                    ,t0.updated_at
                                    ,t0.billing_address,t0.shipping_address,t0.shipping_information
                                    ,t0.payment_method
                                    #,(case when (t9.base_subtotal+t9.base_discount_amount>=50) then 1 else 0 end) as is_vip
                                    ,(SELECT CAST(t0.subtotal AS DECIMAL(9,2))) AS subtotal
                                    ,(SELECT CAST(t0.grand_total AS DECIMAL(9,2))) AS grand_total
                                    ,(SELECT CAST(t0.total_paid AS DECIMAL(9,2))) AS total_paid
                                    ,(SELECT CAST(t0.shipping_and_handling AS DECIMAL(9,2))) AS shipping_and_handling
                                    ,(SELECT CAST(t9.base_discount_amount AS DECIMAL(9,2))) AS base_discount_amount_order
                                    ,t9.total_qty_ordered
                                    
                                    ,t8.email as customer_email
                                    
                                    ,t0.customer_id
                                    ,CONCAT(t8.firstname,' ',t8.lastname) as customer_name
                                    ,t1.parent_item_id
                                    ,t4.attribute_set_id
                                    ,(select attribute_set_name from eav_attribute_set where attribute_set_id= t4.attribute_set_id) as attribute_set_name
                                    ,t1.product_id
                                    ,t9.shipping_method
                                    ,t9.shipping_description
                                    
                                    ,t9.coupon_code
                                    ,t9.coupon_rule_name
                                    ,t9.relation_phone
                                    ,t9.relation_email
                                    ,t9.relation_checked
                                    ,t9.relation_add_date
                                    ,IFNULL(t9.address_verify_status,0) as address_verify_status


                                    ,t1.item_id
                                    ,t1.sku
                                    ,t1.name
                                    ,t1.qty_ordered

                                    ,(SELECT CAST(t1.original_price AS DECIMAL(9,2))) AS original_price
                                    ,(SELECT CAST(t1.price AS DECIMAL(9,2))) AS price
                                    ,(SELECT CAST(t1.base_discount_amount AS DECIMAL(9,2))) AS base_discount_amount_item
                                    ,(case when (t1.price/t1.qty_ordered>=50) then 1 else 0 end) as is_vip
                                    ,(select entity_id from sales_order_address where parent_id=t0.entity_id and address_type='shipping') as shipping_address_id
                                    ,(select entity_id from sales_order_address where parent_id=t0.entity_id and address_type='billing') as billing_address_id

									,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='rim_type')
                                    and entity_id=t1.product_id)) as frame_type
                                    
                                    ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='color')
                                    and entity_id=t1.product_id)) as color
									
									,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='lens_height')
                                    and entity_id=t1.product_id)) as lens_height
                                    
                                    ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='lens_width')
                                    and entity_id=t1.product_id)) as lens_width
                                    ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='bridge')
                                    and entity_id=t1.product_id)) as bridge
                                    ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='temple_length')
                                    and entity_id=t1.product_id)) as temple_length
                                   ,(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='nose_pad')
                                    and entity_id=t1.product_id) as is_has_nose_pad
                                    ,(select count(*) from sales_order_payment where parent_id=t0.entity_id and  address_line1_check ='fail') as is_vailid_pay_addr

                                    ,t1.additional_data
                                    ,t1.profile_id
                                    ,t21.nickname as profile_name
                                    ,t1.profile_prescription_id
                                    ,t1.glasses_prescription_id

                                    ,t2.progressive_type
                                    ,t2.use_for
                                    ,t2.prescription_name
                                    ,t2.rsph
                                    ,t2.lsph
                                    ,t2.rcyl
                                    ,t2.lcyl
                                    ,t2.rax
                                    ,t2.lax
                                    ,t2.pd
                                    ,t2.single_pd
                                    ,t2.rpd
                                    ,t2.lpd
                                    ,t2.rpri
                                    ,t2.lpri
                                    ,t2.rbase
                                    ,t2.lbase
                                    
                                    ,t2.rpri_1 as rpri1
                                    ,t2.lpri_1 as lpri1
                                    ,t2.rbase_1 as rbase1
                                    ,t2.lbase_1 as lbase1
                                    
                                    ,t2.radd
                                    ,t2.ladd
                                    ,t2.exam_date
                                    ,t2.expire_date
                                    ,t2.renew_months
                                    ,t2.updated_at as updated_at_glasses_prescription

                                    ,t3.firstname
                                    ,t3.lastname
                                    ,t3.postcode
                                    ,t3.street
                                    ,t3.city
                                    ,t3.region
                                    ,t3.country_id
                                    ,t3.telephone
                                    
                                    ,t11.image
                                    ,t11.thumbnail
                                    
                                    # 2019.11.15 by guof
                                    ,t9.is_php

                                     #add by rhy
                                    ,(case when locate('is_nonPrescription',t1.product_options)>0 then 1 else 0 end) as is_nonPrescription
                                    ,t1.product_options as product_options
                                    ,t1.has_warranty as item_has_warranty
                                    ,t1.warranty as item_warranty
                                    ,t1.row_total_without_warranty as item_row_total_without_warranty
                                    #add by wj
                                    ,t1.so_type
                                    ,t9.has_warranty
                                    ,t9.warranty
                                    ,t9.row_total_without_warranty
                                    # end

                                    from sales_order_grid t0
                                    inner join sales_order_item t1
                                    on t0.entity_id=t1.order_id
                                    left join sales_order t9
                                    on t0.entity_id=t9.entity_id
                                    left join glasses_prescription t2
                                    on t1.glasses_prescription_id=t2.entity_id
                                    left join sales_order_address t3
                                    on t0.entity_id=t3.parent_id and t3.address_type="shipping"
                                    inner join catalog_product_entity t4
                                    on t1.product_id=t4.entity_id
                                    left join customer_grid_flat t10
                                    on t10.entity_id = t0.customer_id
                                    left join catalog_product_flat_1 t11
                                    on t11.entity_id=t1.product_id
                                    left join profile t21
                                    on t1.profile_id=t21.profile_id
                                    
                                    left join customer_entity t8
                                    on t0.customer_id=t8.entity_id
                                    
'''

# 查询原始验光单sql
sql_query_prescription = '''
select t0.*,t1.product_options from prescription_entity t0
left join sales_order_item t1 on t0.entity_id=t1.profile_prescription_id
where t1.item_id = %s;
'''

# 生成pgorder sql语句的条件
# 2018.10.07 过滤Donation产品
sql_generate_pg_orders_all = "where t0.entity_id > %s and t1.sku !='" + settings.DONATION_SKU + "' order by t1.item_id"
sql_generate_pg_orders_spe = "where t0.increment_id = %s and t1.sku !='" + settings.DONATION_SKU + "'"  # 生成指定pgorder

'''数据维护'''
begin_entity = 100  # 65
end_entity = 160

'''comment'''
base_url = settings.BASE_URL
token_url = 'V1/integration/admin/token'
username = settings.USERNAME
password = settings.PASSWORD
token_data = {
    "username": username,
    "password": password
}
token_header = {'Content-Type': 'application/json'}
url_prefix = 'V1/orders/'
comment_url_suffix = '/comments'

SET_TO_INLAB_URL = 'V1/carts/mine/update_orders'

'''获取N天前的日期，用于查询N天前到现在的数据'''


def date_delta():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-180)
    return timedel


def date_delta_week():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-7)
    return timedel


def date_delta_month():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-30)
    return timedel

def date_delta_month_3():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-90)
    return timedel


'''只生成下单超过两个小时的订单常量设置'''


def set_date():
    set_time = datetime.datetime.utcnow() + datetime.timedelta(hours=-2)
    return set_time
#2020-3-3 ranhy
DICT_SHIPPING_METHODS = {
    'US':[{"id":"standard_standard","label":"STANDARD","description":"Standard - 14-21 days"},{"id":"express_express","label":"EXPRESS","description":"Express - 7-10 days"},{"id":"flatrate_flatrate","label":"Business","description":"Business - Variable"}],
    'CA':[{"id":"canada_express_canada_express","label":"STANDARD","description":"Candada Standard - 14-21 days"}]
}

'''push date'''
push_date_url_suffix = '/shipping-date'

'''rules url'''
rule_url_suffix = '/api/v4.0/calcalates_v4'

# pgorder 消息配置
AT_ACTIVITY_MESSAGE_ONE = 'This order is scheduled in lab, estimated shipping date '
AT_ACTIVITY_MESSAGE_TWO = 'This order is scheduled in lab, estimated shipping '

# 产品图片前缀
PRODUCT_IMAGE_PREPATH = settings.MG_ROOT_URL + settings.PRODUCT_IMAGE_PATH

PAGE_SIZE = 20  # 默认分页
PAGE_SIZE_MORE = 50


'''
authcode加密函数盐值配置，需要与网站配置相同，相互解码
'''
AUTHCODE={
    "secret_key" : ')(*&)(JOIJOIYO^(*&YUFGUFUTRE^FGVL908jk+{}{?:<:<K*Y&^*YU&(UOIMJ',
    "_start_slat" :  '(*UPjq29e0iokLKJ:J%^_)(IOK_+{POIXU@P(*U)(RCIT{PV<KP(#*)(*%(&%(*&@(*&',
    "_end_slat" :  ')(_)*)(IPOJIU^(*&^*&T&))___L{P&^^%$%$%GFVGKJ:LOIoi345poi09f781}\"?><%&O:::P',
}

# Pg Order Status Choices
PG_ORDER_STATUS_CHOICES = (
    ('', ''),
    ('fraud', 'Suspected Fraud'),
    ('processing', 'Processing'),
    ('pending_payment', 'Pending Payment'),
    ('payment_review', 'Payment Review'),
    ('pending', 'Pending'),
    ('holded', 'On Hold'),
    ('complete', 'Complete'),
    ('closed', 'Closed'),
    ('canceled', 'Canceled'),
    ('paypal_canceled_reversal', 'PayPal Canceled Reversal'),
    ('pending_paypal', 'Pending PayPal'),
    ('paypal_reversed', 'PayPal Reversed'),
    ('pending_csr', 'Pending CSR'),
    ('pending_lab', 'Pending Lab'),
    ('r2hold', 'Hold Request '),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('refund', 'Refund'),
)

# Lab Order Status Choices English
LAB_STATUS_CHOICES_EN = (
    ('', 'New Job'),

    ('REQUEST_NOTES', 'Request for frame'),
    ('FRAME_OUTBOUND', 'Frame picked'),
    ('PRINT_DATE', 'Job printed'),
    # ('TINT', '染色'),
    # ('RX_LAB', '车房'),
    # ('ADD_HARDENED', '加硬'),
    # ('COATING', '加膜'),
    ('LENS_OUTBOUND', 'Lens picked'),
    ('LENS_REGISTRATION', 'Lenses received'),
    # ('INITIAL_INSPECTION', 'Lenses Inspection'),
    ('LENS_RETURN', 'Failed lens-inspection'),
    ('LENS_RECEIVE', 'Lens ready'),
    ('ASSEMBLING', 'Being Assembled'),
    ('ASSEMBLED', 'Glasses Assembled'),
    ('GLASSES_RECEIVE', 'Glasses Made'),

    # ('SHAPING', '整形'),
    ('FINAL_INSPECTION', 'QC In Progress'),  # 原终检合格
    ('FINAL_INSPECTION_YES', 'QC Passed'),
    ('FINAL_INSPECTION_NO', 'QC Failed'),
    ('GLASSES_RETURN', 'Glasses Rework'),
    # ('PURGING', '清洗'),
    ('COLLECTION', 'Shipment pairing'),
    ('PRE_DELIVERY', 'Prepare for shipping'),
    ('PICKING', 'Ready to ship'),

    ('ORDER_MATCH', 'Order Pairing'),

    # ('PACKAGE', '包装'),
    ('BOXING', 'Shipment ready'),
    ('SHIPPING', 'Shipped from lab'),
    ('DELIVERED', 'Delivered'),
    # ('COMPLETE', 'Completed'),
    ('ONHOLD', 'On hold'),
    ('CANCELLED', 'Cancelled'),
    ('REDO', 'Being remade'),

    ('R2HOLD', 'Request to hold'),
    ('R2CANCEL', 'Request to cancel'),
    ('CLOSED', 'Closed')
)

# Lab Order Status Choices
LAB_STATUS_CHOICES = (
    ('', '新订单'),

    ('REQUEST_NOTES', '出库申请'),
    ('FRAME_OUTBOUND', '镜架出库'),
    ('PRINT_DATE', '单证打印'),
    # ('TINT', '染色'),
    # ('RX_LAB', '车房'),
    # ('ADD_HARDENED', '加硬'),
    # ('COATING', '加膜'),
    ('LENS_OUTBOUND', '镜片出库'),
    ('LENS_REGISTRATION', '来片登记'),
    # ('INITIAL_INSPECTION', '镜片初检'),
    ('LENS_RETURN', '镜片退货'),
    ('LENS_RECEIVE', '镜片收货'),
    ('ASSEMBLING', '待装配'),
    ('ASSEMBLED', '装配完成'),
    ('GLASSES_RECEIVE', '成镜收货'),

    # ('SHAPING', '整形'),
    ('FINAL_INSPECTION', '终检'),  # 原终检合格
    ('FINAL_INSPECTION_YES', '终检合格'),
    ('FINAL_INSPECTION_NO', '终检不合格'),
    ('GLASSES_RETURN', '成镜返工'),
    # ('PURGING', '清洗'),
    ('COLLECTION', '归集'),
    ('PRE_DELIVERY', '预发货'),
    ('PICKING', '已拣配'),

    ('ORDER_MATCH', '订单配对'),

    # ('PACKAGE', '包装'),
    ('BOXING', '装箱'),
    ('SHIPPING', '已发货'),
    ('DELIVERED', '妥投'),
    # ('COMPLETE', '完成'),
    ('ONHOLD', '暂停'),
    ('CANCELLED', '取消'),
    ('REDO', '重做'),

    ('R2HOLD', '申请暂停'),
    ('R2CANCEL', '申请取消'),
    ('CLOSED', '关闭')
)


