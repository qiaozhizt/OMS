# -*- coding: utf-8 -*-

#
# file name: order_controller.py
# 2018.06.19 created by guof.
# 关于 PgOrder / PgOrderItem / LabOrder 的控制类
#

from django.db import connections
from django.db import transaction
from decimal import *
import urllib2
import requests
import logging
import json

from django.http import HttpResponse, JsonResponse

from util.db_helper import *
from util.time_delta import *
from util.dict_helper import *
from util.format_helper import *
from util.response import *

from pg_oms.settings import *

import oms.const
from api.models import response_address

from oms.models.order_models import *
from oms.models.response_models import *
import re

from api.models import DingdingChat
from tracking.models import ai_log_control

# Pg Order Controller Class
class PgOrderController:
    black_set = set()

    # 生成 Pg Orders
    def gen_pgorder(self, results):
        """生成pgorder"""

        po = PgOrder()
        flag = False
        try:
            pgorder = po.query_by_id(results.increment_id)
        except:
            flag = True
            po.order_number = results.increment_id
            logging.debug("pg-->order_number==>" + str(results.increment_id))
            po.base_entity = results.entity_id
            logging.debug("pg-->base_entity==>%s" % results.entity_id)
            po.customer_id = results.customer_id
            po.coupon_code = results.coupon_code
            po.coupon_rule_name = results.coupon_rule_name

            po.billing_address_id = results.billing_address_id
            po.shipping_address_id = results.shipping_address_id

            po.customer_name = results.customer_name
            if results.customer_id == 200053 or results.customer_id == '200053':
                po.status = 'holded'
            else:
                po.status = results.status

            po.web_status = results.status
            po.email = results.customer_email

            # 联系电话，联系邮件，添加日期  2018-08-29 ranhy
            po.relation_email = results.relation_email
            po.relation_phone = results.relation_phone
            po.relation_checked = results.relation_checked
            po.relation_add_date = results.relation_add_date

            # magneto地址是换行符分隔stree ranhy
            str_street = results.street.encode('utf-8')
            sec_str = '\n'
            arr_street = str_street.split(sec_str)
            po.street = arr_street[0]
            if len(arr_street) > 1:
                po.street2 = arr_street[1]
            po.address_verify_status = results.address_verify_status

            po.order_date = results.created_at
            po.order_datetime = results.created_at
            po.subtotal = results.subtotal
            po.grand_total = results.grand_total
            if results.total_paid <> None:
                po.total_paid = results.total_paid

            po.shipping_and_handling = results.shipping_and_handling
            po.base_discount_amount_order = results.base_discount_amount_order
            po.total_qty_ordered = Decimal(results.total_qty_ordered).quantize(Decimal('0.00'))
            po.firstname = results.firstname
            po.lastname = results.lastname
            po.postcode = results.postcode
            po.phone = results.telephone

            # warranty add by ranhy 2019-09-02
            po.warranty = results.warranty
            po.has_warranty = results.has_warranty
            po.row_total_without_warranty = results.row_total_without_warranty

            # 2019.12.17 by guof.
            # origin order entity & order number

            if results.is_clone == 1 or results.is_clone == "1":
                po.is_remake_order = True
                try:
                    po.origin_order_entity = results.clone_order_id
                    po.origin_order_number = results.clone_order_number
                except Exception as ex:
                    po.origin_order_number = 'An error occurred while getting origin order information [%s]' % str(ex)

            po.city = results.city
            po.region = results.region
            po.country_id = results.country_id
            po.shipping_method = results.shipping_method
            if results.shipping_method == 'express_express':
                po.ship_direction = 'EXPRESS'
                po.promised_ship_date = (
                    results.created_at + datetime.timedelta(days=8)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            elif results.shipping_method == 'standard_standard':
                po.ship_direction = 'STANDARD'
                po.promised_ship_date = (
                    results.created_at + datetime.timedelta(days=16)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            elif results.shipping_method == 'flatrate_flatrate':
                po.ship_direction = 'FLATRATE'
                po.promised_ship_date = (
                    results.created_at + datetime.timedelta(days=16)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            elif results.shipping_method == 'canada_express_canada_express':
                po.ship_direction = 'CA_EXPRESS'
                po.promised_ship_date = (
                    results.created_at + datetime.timedelta(days=8)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            else:
                po.ship_direction = results.shipping_method

            if results.country_id == 'CN':
                po.ship_direction = 'EMPLOYEE'
                po.promised_ship_date = (
                    results.created_at + datetime.timedelta(days=16)).strftime(
                    "%Y-%m-%d %H:%M:%S")

            if results.is_vip == 1:
                po.is_vip = True
            else:
                po.is_vip = False

            # 2019.11.15 by guof.
            if results.is_php == 1:
                po.tag = 'PHP'

            po.shipping_description = results.shipping_description
            po.web_created_at = results.created_at
            po.web_updated_at = results.updated_at
            logging.debug("pg-->web_updated_at==>%s" % results.updated_at)
            po.save()

            self.fraud_check(po)

            # 2019.10.14 by guof.
            # send dingding message to test chat
            # nw = db_convert2bj(po.create_at)
            # ddc = DingdingChat()
            # ddc.send_text_to_chat('chatbbb102b95b3b870fd402a9bb8931c5af','New Order: [%s][%s]' % (po.order_number,nw))

            logging.debug("Pg Order Saved ....")
        return po, flag

    # 生成 Pg Order Items
    def gen_pgorderitem(self, results, po):
        # add by ranhy 2019-09-02
        rx_error_info = ''
        # end
        nonelist = []
        for k in range(len(results)):
            if results[k].parent_item_id == None:
                nonelist.append(results[k])
        logging.debug('nonelist ---------------------------------------->')
        product_index = 0
        for y in range(len(nonelist)):
            for i in range(0, nonelist[y].qty_ordered):
                product_index = product_index + 1
                pgorderitem = PgOrderItem()
                # pgorder.quantity = nonelist[y].quantity
                if nonelist[y].rsph == None:
                    pgorderitem.od_sph = 0.00
                else:
                    pgorderitem.od_sph = nonelist[y].rsph
                logging.debug("od_sph==>" + str(nonelist[y].rsph))

                if nonelist[y].rcyl == None:
                    pgorderitem.od_cyl = 0.00
                else:
                    pgorderitem.od_cyl = nonelist[y].rcyl
                if nonelist[y].rax == None:
                    pgorderitem.od_axis = 0
                else:
                    pgorderitem.od_axis = nonelist[y].rax

                if nonelist[y].lsph == None:
                    pgorderitem.os_sph = 0.00
                else:
                    pgorderitem.os_sph = nonelist[y].lsph

                if nonelist[y].lcyl == None:
                    pgorderitem.os_cyl = 0.00
                else:
                    pgorderitem.os_cyl = nonelist[y].lcyl

                if nonelist[y].lax == None:
                    pgorderitem.os_axis = 0
                else:
                    pgorderitem.os_axis = nonelist[y].lax

                if nonelist[y].rpd == None:
                    pgorderitem.od_pd = 0.00
                else:
                    pgorderitem.od_pd = nonelist[y].rpd

                if nonelist[y].lpd == None:
                    pgorderitem.os_pd = 0.00
                else:
                    pgorderitem.os_pd = nonelist[y].lpd

                if nonelist[y].pd == None:
                    pgorderitem.pd = 0.00
                else:
                    pgorderitem.pd = nonelist[y].pd

                if nonelist[y].radd == None:
                    pgorderitem.od_add = 0.00
                else:
                    pgorderitem.od_add = nonelist[y].radd

                if nonelist[y].ladd == None:
                    pgorderitem.os_add = 0.00
                else:
                    pgorderitem.os_add = nonelist[y].ladd

                #调整棱镜对应
                odbase = nonelist[y].rbase
                osbase = nonelist[y].lbase
                odbase1 = nonelist[y].rbase1
                osbase1 = nonelist[y].lbase1

                if odbase in ['In', 'Out']:
                    pgorderitem.od_prism = nonelist[y].rpri
                    pgorderitem.od_base = odbase.upper()
                elif odbase in ['Up', 'Down']:
                    pgorderitem.od_prism = 0.00
                    pgorderitem.od_base = ''
                    pgorderitem.od_prism1 = nonelist[y].rpri
                    pgorderitem.od_base1 = odbase.upper()
                else:
                    pgorderitem.od_prism = 0.00
                    pgorderitem.od_base = ''

                if osbase in ['In', 'Out']:
                    pgorderitem.os_prism = nonelist[y].lpri
                    pgorderitem.os_base = osbase.upper()
                elif osbase in ['Up', 'Down']:
                    pgorderitem.os_prism = 0.00
                    pgorderitem.os_base = ''
                    pgorderitem.os_prism1 = nonelist[y].lpri
                    pgorderitem.os_base1 = osbase.upper()
                else:
                    pgorderitem.os_prism = 0.00
                    pgorderitem.os_base = ''

                if odbase1 in ['In', 'Out']:
                    pgorderitem.od_prism = nonelist[y].rpri1
                    pgorderitem.od_base = odbase1.upper()
                elif odbase1 in ['Up', 'Down']:
                    pgorderitem.od_prism1 = nonelist[y].rpri1
                    pgorderitem.od_base1 = odbase1.upper()
                else:
                    if odbase not in ['Up', 'Down']:
                        pgorderitem.od_prism1 = 0.00
                        pgorderitem.od_base1 = ''

                if osbase1 in ['In', 'Out']:
                    pgorderitem.os_prism = nonelist[y].lpri1
                    pgorderitem.os_base = osbase1.upper()
                elif osbase1 in ['Up', 'Down']:
                    pgorderitem.os_prism1 = nonelist[y].lpri1
                    pgorderitem.os_base1 = osbase1.upper()
                else:
                    if osbase not in ['Up', 'Down']:
                        pgorderitem.os_prism1 = 0.00
                        pgorderitem.os_base1 = ''
                #################
                # if nonelist[y].rpri == None:
                #     pgorderitem.od_prism = 0.00
                # else:
                #     pgorderitem.od_prism = nonelist[y].rpri
                #
                # if nonelist[y].rbase == None:
                #     pgorderitem.od_base = ''
                # else:
                #     odbase = nonelist[y].rbase
                #     pgorderitem.od_base = odbase.upper()
                # if nonelist[y].lpri == None:
                #     pgorderitem.os_prism = 0.00
                # else:
                #     pgorderitem.os_prism = nonelist[y].lpri
                #
                # if nonelist[y].lbase == None:
                #     pgorderitem.os_base = ''
                # else:
                #     osbase = nonelist[y].lbase
                #     pgorderitem.os_base = osbase.upper()

                # if nonelist[y].rpri1 == None:
                #     pgorderitem.od_prism1 = 0.00
                # else:
                #     pgorderitem.od_prism1 = nonelist[y].rpri1
                #
                # if nonelist[y].rbase1 == None:
                #     pgorderitem.od_base1 = ''
                # else:
                #     odbase1 = nonelist[y].rbase1
                #     pgorderitem.od_base1 = odbase1.upper()

                # if nonelist[y].lpri1 == None:
                #     pgorderitem.os_prism1 = 0.00
                # else:
                #     pgorderitem.os_prism1 = nonelist[y].lpri1
                #
                # if nonelist[y].lbase1 == None:
                #     pgorderitem.os_base1 = ''
                # else:
                #     osbase1 = nonelist[y].lbase1
                #     pgorderitem.os_base1 = osbase1.upper()
                if nonelist[y].lens_height <> None:
                    pgorderitem.lens_height = nonelist[y].lens_height

                if nonelist[y].lens_width <> None:
                    pgorderitem.lens_width = nonelist[y].lens_width

                if nonelist[y].bridge <> None:
                    pgorderitem.bridge = nonelist[y].bridge

                if nonelist[y].is_has_nose_pad <> None:
                    pgorderitem.is_has_nose_pad = nonelist[y].is_has_nose_pad

                # add lee 2018.8.21 oms_pgorderitem表增加progressive_type辽段
                if nonelist[y].progressive_type <> None:
                    pgorderitem.progressive_type = nonelist[y].progressive_type
                else:
                    pgorderitem.progressive_type = ""
                    # end add

                if nonelist[y].temple_length <> None:
                    pgorderitem.temple_length = nonelist[y].temple_length

                if nonelist[y].lens_width <> None and nonelist[y].bridge <> None:
                    if nonelist[y].temple_length <> None:
                        pgorderitem.size = nonelist[y].lens_width + '-' + nonelist[y].bridge + '-' + nonelist[
                            y].temple_length
                    else:
                        pgorderitem.size = nonelist[y].lens_width + '-' + nonelist[y].bridge + '-' + '0'
                # new
                pgorderitem.quantity = 1#nonelist[y].qty_ordered
                if nonelist[y].is_vip == 1:
                    pgorderitem.is_vip = True
                else:
                    pgorderitem.is_vip = False

                if nonelist[y].is_php == 1:
                    pgorderitem.tag = 'PHP'

                if nonelist[y].use_for <> None:
                    pgorderitem.used_for = nonelist[y].use_for

                pgorderitem.shipping_method = nonelist[y].shipping_method
                pgorderitem.shipping_description = nonelist[y].shipping_description

                if nonelist[y].shipping_method == 'express_express':
                    pgorderitem.ship_direction = 'EXPRESS'
                    pgorderitem.promised_ship_date = (
                        nonelist[y].created_at + datetime.timedelta(days=8)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                elif nonelist[y].shipping_method == 'standard_standard':
                    pgorderitem.ship_direction = 'STANDARD'
                    pgorderitem.promised_ship_date = (
                        nonelist[y].created_at + datetime.timedelta(days=16)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                elif nonelist[y].shipping_method == 'flatrate_flatrate':
                    pgorderitem.ship_direction = 'FLATRATE'
                elif nonelist[y].shipping_method == 'canada_express_canada_express':
                    pgorderitem.ship_direction = 'CA_EXPRESS'
                    pgorderitem.promised_ship_date = (
                        nonelist[y].created_at + datetime.timedelta(days=8)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pgorderitem.ship_direction = nonelist[y].shipping_method

                if nonelist[y].country_id == 'CN':
                    pgorderitem.ship_direction = 'EMPLOYEE'
                    pgorderitem.promised_ship_date = (
                        nonelist[y].created_at + datetime.timedelta(days=16)).strftime(
                        "%Y-%m-%d %H:%M:%S")

                # city,region
                pgorderitem.city = nonelist[y].city
                pgorderitem.region = nonelist[y].region

                # prescription_type,prescription_nameprescription_id
                pgorderitem.profile_id = nonelist[y].profile_id
                pgorderitem.profile_name = nonelist[y].profile_name
                pgorderitem.profile_prescription_id = nonelist[y].profile_prescription_id
                pgorderitem.prescription_id = nonelist[y].glasses_prescription_id
                pgorderitem.prescription_name = nonelist[y].prescription_name
                # pgorderitem.prescription_type = nonelist[y].prescription_type

                # warranty add by ranhy 2019-09-02
                pgorderitem.warranty = nonelist[y].warranty
                pgorderitem.has_warranty = nonelist[y].has_warranty
                pgorderitem.row_total_without_warranty = nonelist[y].row_total_without_warranty
                pgorderitem.product_options = nonelist[y].product_options
                pgorderitem.is_nonPrescription = nonelist[y].is_nonPrescription
                # add by wj
                pgorderitem.so_type = nonelist[y].so_type
                rx_error_info = ''
                if (pgorderitem.product_options):
                    if (pgorderitem.is_nonPrescription and (
                                    pgorderitem.profile_prescription_id or pgorderitem.prescription_id or pgorderitem.prescription_name)):
                        rx_error_info += 'sku:%sRX疑似有问题\n' % nonelist[y].sku

                    if (not pgorderitem.is_nonPrescription and (
                                not pgorderitem.profile_prescription_id or not pgorderitem.prescription_id)):
                        rx_error_info += 'sku:%s验光单丢失\n' % nonelist[y].sku

                    elif (not pgorderitem.is_nonPrescription and not pgorderitem.pd and (
                                not pgorderitem.os_pd and not pgorderitem.od_pd)):
                        rx_error_info += 'sku:%spd丢失\n' % nonelist[y].sku

                    if (pgorderitem.used_for != 'PROGRESSIVE' and (pgorderitem.od_add != 0 or pgorderitem.os_add != 0)):
                        rx_error_info += 'sku:%s验光单非渐近出现ADD，验光单错误\n' % nonelist[y].sku

                    if (po.coupon_code == 'PG-INTERNAL'):
                        rx_error_info += '内部订单，请确认后取消\n'
                #add by ranhy 2020-09-27
                if(nonelist[y].is_nonPrescription and nonelist[y].is_vailid_pay_addr):
                    rx_error_info += '无验光单且strip支付地址校验失败，需核对！\n'


                pgorderitem.product_index = product_index#y

                pgorderitem.country = nonelist[y].country_id
                pgorderitem.order_number = nonelist[y].increment_id

                pgorderitem.item_id = nonelist[y].item_id
                pgorderitem.product_id = nonelist[y].product_id

                # 2020.03.12 by guof. 勿论其他属性如何，先把frame 属性 颜色等信息填入数据库
                pgorderitem.frame = nonelist[y].sku
                pgorderitem.name = nonelist[y].name
                pgorderitem.frame_type = nonelist[y].frame_type
                pgorderitem.color = nonelist[y].color

                # 2020.04.13 by guof. OMS-729
                # 2020.04.15 调整 增加4209G07
                # 由于是暂时性调整 此处使用hard code
                # 如果大批量使用的时候，需要启用之前设计的Stock Order流程，并删除此段代码！
                # --------------------start--------------------
                # 该段代码在以下两款SKU售罄之后可以删除
                # 如果Frame SKU 等于 1319C09或1320C09 则自动hold 标记为 STOCK_ORDER
                if '1319C09' in pgorderitem.frame or '1320C09' in pgorderitem.frame \
                        or '4209G07' in pgorderitem.frame:
                    pgorderitem.tag += ',STOCK_ORDER'
                    po.instruction = 'STOCK_ORDER'
                    po.save()

                    ding_msg = 'atention please, order: %s, frame:%s is STOCK_ORDER' % (
                        po.order_number,
                        pgorderitem.frame)
                    dc = DingdingChat()

                    dc.send_text_to_chat('chat72dbc9260ec82f1f871d55ad42e51966', ding_msg)
                # --------------------end--------------------

                pgorderitem.order_date = nonelist[y].created_at
                pgorderitem.order_datetime = nonelist[y].created_at
                if nonelist[y].single_pd == 0:
                    pgorderitem.is_singgle_pd = False
                else:
                    pgorderitem.is_singgle_pd = True
                relateproduct = []

                pgorderitem.pg_order_entity = po
                pgorderitem.original_price = nonelist[y].original_price
                pgorderitem.price = nonelist[y].price
                pgorderitem.base_discount_amount_item = nonelist[y].base_discount_amount_item

                pgorderitem.status = nonelist[y].status

                for h in range(len(results)):
                    if results[h].parent_item_id == nonelist[y].item_id:
                        relateproduct.append(results[h])

                # 2019.12.18 by guof. OMS-541
                # 增加Attribute Set Id，识别产品类型

                pgorderitem.attribute_set_id = nonelist[y].attribute_set_id
                pgorderitem.attribute_set_name = nonelist[y].attribute_set_name

                if pgorderitem.attribute_set_name == 'Glasses' or pgorderitem.attribute_set_name == 'Goggles':
                    # 如果是 Glasses ，保持原有逻辑不变
                    for x in range(len(relateproduct)):
                        if x == 0:
                            # sku = relateproduct[x].sku
                            # frame = sku[1:len(sku)]

                            if relateproduct[x].image <> None:
                                pgorderitem.image = relateproduct[x].image

                            if relateproduct[x].thumbnail <> None:
                                pgorderitem.thumbnail = relateproduct[x].thumbnail

                            pgorderitem.frame = relateproduct[x].sku
                            pgorderitem.name = relateproduct[x].name

                            pgorderitem.frame_type = relateproduct[x].frame_type
                            pgorderitem.color = relateproduct[x].color

                            logging.debug("frame==>" + str(relateproduct[x].sku))

                        # 2020.01.08 by guof. OMS-575
                        # 调整订单生成的规则，以Attribute Set Name作为筛选条件
                        elif x > 0:
                            if relateproduct[x].attribute_set_name == "Lenss":
                                logging.debug("x==1")
                                pgorderitem.lens_sku = relateproduct[x].sku

                                # 2019.11.20 by guof
                                if pgorderitem.lens_sku == 'SB591' or pgorderitem.lens_sku == 'SB592':
                                    pgorderitem.lens_sku = 'SB59'
                                    pgorderitem.tag = relateproduct[x].sku

                                pgorderitem.lens_name = relateproduct[x].name
                                logging.debug("lens_sku==>" + str(relateproduct[x].sku))

                                # lens verified by guof 2019.09.09
                                if (pgorderitem.od_add != 0 or pgorderitem.os_add != 0  # add
                                    or pgorderitem.od_prism or pgorderitem.os_prism or pgorderitem.od_prism1 or pgorderitem.os_prism1  # 棱镜
                                    or (abs(pgorderitem.od_cyl) > 2 or abs(pgorderitem.os_cyl > 2)  # 散光大于200
                                        or abs(pgorderitem.od_sph - pgorderitem.os_sph) > 3)  # sph相差大于300
                                    ):
                                    try:
                                        # 是太阳镜时，染色由太阳镜最后一位和镜片sku组合，如果是偏光镜片，则不组合
                                        temp_lens_sku = pgorderitem.lens_sku
                                        data = {"sku": temp_lens_sku}
                                        headers = {'Content-Type': 'application/json'}
                                        isplr_res = requests.post(PG_SYNC_IS_POLARIZED_URL, data=json.dumps(data),
                                                                  headers=headers)
                                        json_res = json.loads(isplr_res.text)
                                        r_code = json_res.get('code', '')
                                        if (r_code):
                                            r_is_polarized = json_res.get('is_polarized')
                                            if len(pgorderitem.frame) == 9 and r_is_polarized:
                                                temp_lens_sku = pgorderitem.lens_sku + pgorderitem.frame[-1]
                                        lens = PgProduct.objects.get(sku=temp_lens_sku)
                                        if not lens.is_rx_lab:
                                            rx_error_info += '镜片sku:%s生成的验光单应该使用车房未使用车房片\n' % pgorderitem.lens_sku
                                    except:
                                        rx_error_info += '镜片sku:%s错误\n' % pgorderitem.lens_sku

                            # 2020.01.08 by guof. OMS-575
                            # coating_sku default value set to VCAS
                            if relateproduct[x].attribute_set_name == "Coating":
                                pgorderitem.coating_sku = relateproduct[x].sku
                                pgorderitem.coating_name = relateproduct[x].name
                                logging.debug("coating_sku==>" + str(relateproduct[x].sku))
                            if relateproduct[x].attribute_set_name == "Tint":
                                pgorderitem.tint_sku = relateproduct[x].sku
                                pgorderitem.tint_name = relateproduct[x].name
                                logging.debug("tint_sku==>" + str(relateproduct[x].sku))
                            if relateproduct[x].attribute_set_name == "PAL_Design":
                                pgorderitem.pal_design_sku = relateproduct[x].sku
                                pgorderitem.pal_design_name = relateproduct[x].name
                                logging.debug("pal_design_sku==>" + str(relateproduct[x].sku))
                            if relateproduct[x].attribute_set_name == "Special_Handling":
                                pgorderitem.special_handling_sku = relateproduct[x].sku
                                pgorderitem.special_handling_name = relateproduct[x].name
                                # 把美薄特殊处理转换成中文保存在 special_handling 中
                                # (D-THIN, D-THINM) -> (普通美薄, 渐进片美薄)
                                thin_handling = {
                                    'D-THIN': '普通美薄',
                                    'D-THINM': '渐进片美薄',
                                    'D-ERR': '未知处理方式'
                                }
                                try:
                                    pgorderitem.special_handling = "%s" % thin_handling[relateproduct[x].sku]
                                except:
                                    pgorderitem.special_handling = "%s" % thin_handling['D-ERR']
                # 2020.03.06 by guof. 修复由于attribute_set_name可能为NULL产生的bug
                # elif pgorderitem.attribute_set_name:
                #     if "SPECIFIED" in pgorderitem.attribute_set_name.upper():
                #         pgorderitem.frame = nonelist[y].sku
                #         pgorderitem.name = nonelist[y].name
                #         pgorderitem.frame_type = nonelist[y].frame_type
                #         pgorderitem.color = nonelist[y].color
                # 2020.03.18 by wj. 修复图片不生成bug
                else:
                    for x in range(len(relateproduct)):
                        if x == 0:

                            if relateproduct[x].image:
                                pgorderitem.image = relateproduct[x].image

                            if relateproduct[x].thumbnail:
                                pgorderitem.thumbnail = relateproduct[x].thumbnail

                            pgorderitem.frame = relateproduct[x].sku
                            pgorderitem.name = relateproduct[x].name

                            pgorderitem.frame_type = relateproduct[x].frame_type
                            pgorderitem.color = relateproduct[x].color

                # rx error message saved.

                # 2019.12.25 by guof. OMS-555
                # 增加对 Accs Order 的判断，只有Glasses类型的订单才做判断
                # 2020-09-27,update by ranhy 13=>Glasses
                if rx_error_info and pgorderitem.attribute_set_name == 'Glasses':
                    pgorderitem.comments_inner += rx_error_info
                    po.status = "holded"
                    po.save()
                from oms.controllers.pg_order_controller import pg_order_controller
                poc = pg_order_controller()
                data_dict = {
                    "lens_sku": pgorderitem.lens_sku,
                    "tint_name": pgorderitem.tint_name
                }
                order_type = poc.get_order_type(data_dict)
                pgorderitem.order_type = order_type
                pgorderitem.save()

                # calculate diameter
                logging.debug('calculate diameter begin ....')

                try:
                    # pgi = PgOrderItem.objects.get(id=pgorderitem.id)

                    pre = pgorderitem.get_prescritpion
                    pre_dict = utilities.convert_to_dict(pre)
                    body = {
                        "product_sku": pgorderitem.frame,
                        "prescription": pre_dict
                    }
                    body = json.dumps(body, cls=DateEncoder)
                    logging.debug("body==>%s" % body)

                    req = urllib2.Request(url=CALCULATE_DIAMETER_URL_V2, data=body, headers=token_header)
                    res = urllib2.urlopen(req)
                    resp = res.read()

                    resp = json.loads(resp)
                    logging.debug('respones: %s' % resp)

                    pgorderitem.dia_1 = resp['dia_1']
                    pgorderitem.dia_2 = resp['dia_2']
                    pgorderitem.save()
                except Exception as e:
                    logging.debug('exception: %s' % e)

                logging.debug('calculate diameter end ....')

    # 生成 Pg Order 的 Special Instructions.
    def gen_pgorder_speical_instructions(self):
        pass

    # 执行 Review / Approve 等 Actions
    def actions(self, request, order_number, action_value):
        rv = ''
        try:
            order_number = str(order_number)

            pgo = PgOrder.objects.get(order_number=order_number)

            if pgo.status <> 'processing':
                return 'The order status is not processing, and Laborder cannot be generated.'

            if pgo.is_inlab == False:
                if action_value == 'review':
                    if pgo.status_control == 'REVIEWED' or pgo.status_control == 'APPROVED':
                        return "Your order has been reviewed or approved!"

                    self.tracking_operation_log(request, pgo, action_value, "status_control", "REVIEWED")
                    pgo.status_control = 'REVIEWED'

                elif action_value == 'approve':
                    if pgo.status_control == 'APPROVED':
                        return "Your order has been approved!"

                    self.tracking_operation_log(request, pgo, action_value, "status_control", "APPROVED")
                    pgo.status_control = 'APPROVED'

                elif action_value == 'cancel_review':
                    if not pgo.status_control == 'REVIEWED':
                        return "Your order hasn't been reviewed!"
                    self.tracking_operation_log(request, pgo, action_value, "status_control", "")
                    pgo.status_control = ''

                pgo.save()
                return "Success"
        except:
            rv = 'exception'

        return rv

    def tracking_operation_log(self, request, pgo, action_value, fields, new_value):
        origin_value = pgo.status_control
        from api.controllers.tracking_controllers import tracking_operation_controller
        tc = tracking_operation_controller()
        tc.tracking(
            pgo.type, pgo.id,
            pgo.order_number,
            action_value,
            fields,
            request.user,
            origin_value,
            new_value,
            None,
            None,
        )

    # 由 Pg Order 生成 Lab Orders
    def generate_lab_orders(self, order_number, extends_paras=None):
        if order_number:
            order_number = order_number.strip()
        else:
            return "Order Number missed!"

        logging.debug("order_number==>" + str(order_number))

        po = PgOrder.objects.get(order_number=order_number)
        #判断是否是在黑名单中
        if len(self.black_set) == 0:
            self.add_black()

        if po.email in self.black_set:
            old_comments = po.comments
            po.comments = old_comments + "\n 此客户在黑名单中"
            po.save()
            return '此客户在黑名单中'
        # 2020.02.24 by guof. OMS-627
        if not extends_paras:
            if po.status <> 'processing':
                return 'The order status is not processing, and Lab order can not be generated.'
        else:
            logging.debug(extends_paras)
            ignore_fraud_check = extends_paras.get('ignore_fraud_check', '')
            if ignore_fraud_check != '1':
                if po.status <> 'processing':
                    return 'The order status is not processing, and Lab order can not be generated.'

            msg = 'Attention please, Pg Order[%s] status is [fraut], but it has been generated lab orders ....' % \
                  po.order_number
            dc = DingdingChat()
            dc.send_text_to_chat('chat72dbc9260ec82f1f871d55ad42e51966', msg)

        if po.is_inlab == False:

            try:
                with transaction.atomic():

                    '''pgorderitem规定完成时间，取最晚的一个时间加一天'''
                    date_list = po.generate_lab_orders()
                    logging.debug("-----------------------------------%s" % date_list)

                    # 2019.12.25 by guof. OMS-544
                    if date_list:
                        max_date = max(date_list)
                        logging.debug("max_date==>%s" % max_date)
                        if max_date:
                            po.targeted_ship_date = (
                                datetime.datetime.strptime(max_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(
                                    days=1)).strftime(
                                "%Y-%m-%d %H:%M:%S")
                            logging.debug("po.targete_ship_date==>%s" % po.targeted_ship_date)
                            logging.debug(type(po.targeted_ship_date))

                            tsd = datetime.datetime.strptime(po.targeted_ship_date,
                                                             '%Y-%m-%d %H:%M:%S')  # 将日期转换为datetime类型
                            message_one = AT_ACTIVITY_MESSAGE_ONE + tsd.strftime('%m/%d/%Y')
                            # psd = datetime.datetime.strptime(po.promised_ship_date, '%Y-%m-%d %H:%M:%S')
                            message_two = AT_ACTIVITY_MESSAGE_TWO + tsd.strftime(
                                '%m/%d/%Y') + '—' + po.promised_ship_date.strftime('%m/%d/%Y')
                            oa = OrderActivity()
                            oa.add_activity(po.type, po.id, po.order_number, 'ADD Comment', 0, 'system', message_one)
                            oa = OrderActivity()
                            oa.add_activity(po.type, po.id, po.order_number, 'ADD Comment', 0, 'system', message_two)
                            po.save()
                            '''给pgorderitem添加targeted_ship_date'''
                            pois = PgOrderItem.objects.filter(order_number=order_number)
                            for poim in pois:
                                poim.targeted_ship_date = po.targeted_ship_date
                                poim.save()
                '''向服务器传送地址'''
                logging.debug("----开始发送地址----")
                entities = []
                entities.append(po.order_number)

                entities = json.dumps(entities)

                self.pgorder_address_verified(entities)

                # order_number = str(order_number)
                self.shipment_server(order_number, False)

                # set to inlab
                self.set_to_inlab(order_number)

                data = {}
                data['order_number'] = po.order_number
                data['promised_date'] = po.promised_ship_date
                data['targeted_date'] = po.targeted_ship_date

                try:
                    if settings.NOTICED_CUSTOMER_EST_DATE:
                        self.post_estimate_date(None, data)
                except:
                    pass

                return "Success"
            except Exception as e:
                logging.debug("Error==>%s" % e)
                transaction.rollback()
                return str(e)
        else:
            return "Laborder is generated and cannot be repeated"

    # 调用 Ship 系统接口，生成 Shipments
    def shipment_server(self, order_number=None, toggle=True):
        ailog = ai_log_control()  # AI操作日志
        try:
            orderNumber = str(order_number)
            logging.debug("-------------order_number------------>%s" % orderNumber)
            shp = shipment(orderNumber)
            jsonShipment = shp.post_shipment()  # 返回json格式shipment
            logging.debug(jsonShipment)
            if jsonShipment == None:
                return 'Generate the pgorder and then execute shipping.'
            requrl = ADDRESS_URL
            headers = {'Content-Type': 'application/json'}
            req = urllib2.Request(url=requrl, data=jsonShipment, headers=headers)
            res = urllib2.urlopen(req)
            r_data = json.loads(res.read())
            print(r_data)

            if r_data:
                if r_data[0]['verify'] == "success":
                    pg_order = PgOrder.objects.get(order_number=orderNumber)
                    pg_order.is_shiped_api = True
                    pg_order.save()
                    if toggle:
                        ailog.add('pgorderitem', '',order_number, '自动下单', 'shipment_serve', '', '', '200',
                                  'OK', 'YES', 'success')
                        return 'success'
                    logging.debug("-----地址发送成功------")
                else:
                    if toggle:
                        ailog.add('pgorderitem', '', order_number, '自动下单', 'shipment_server', '', '', '500',
                                  'ERROR', 'YES', '地址发送失败！！！！')
                        return 'Failed'
                    logging.debug("！！！！地址发送失败！！！！")

            else:
                if toggle:
                    ailog.add('pgorderitem', '', order_number, '自动下单', 'shipment_server', '', '', '500',
                              'ERROR', 'YES', 'Failed, the return value is empty.')
                    return 'Failed, the return value is empty.'
                logging.debug("！！！！返回值为空！！！！")
        except Exception as e:
            ailog.add('pgorderitem', '', order_number, '自动下单', 'shipment_server', '', '', '500',
                      'ERROR', 'YES', e)
            if toggle:
                return "fail"
            logging.debug('---------请求url失败------------')

    def getToken(self):
        get_token_url = BASE_URL + token_url
        api_response = requests.post(get_token_url, data=json.dumps(token_data), headers=token_header)
        return api_response.text.replace('"', '')

    # 调用 状态更新接口 系统接口，生成 In Lab 状态
    def set_to_inlab(self, order_number=None, toggle=True):
        ailog = ai_log_control()  # AI操作日志
        try:
            orderNumber = str(order_number)
            token = self.getToken()
            send_comment_url = BASE_URL + SET_TO_INLAB_URL
            http_headers = {
                'Authorization': 'Bearer %s' % token,
                'Content-Type': 'application/json'
            }

            send_data = {
                'order_number': orderNumber,
                'substate': 'In Lab'
            }
            api_response = requests.post(send_comment_url, data=json.dumps(send_data), headers=http_headers,timeout=10, verify=False)
            logging.info(api_response.text)
            ailog.add('pgorderitem', '',order_number, '自动下单', 'set_to_inlab', '', '', '200',
                      'OK', 'YES', api_response.text)
            return api_response.text

        except Exception as e:
            logging.debug(str(e))
            ailog.add('pgorderitem', '',order_number, '自动下单', 'set_to_inlab','', '', '500',
                      'ERROR', 'YES', e)

    def generate_order_addtional(self):
        objs = OrderAddtional.objects.all().order_by('-id')
        obj_max_entity = 0
        if len(objs) > 0:
            obj_max_entity = objs[0].mg_id

        logging.debug('----------------------------------------')

        logging.info('current oms additional id: %s' % obj_max_entity)

        obj = OrderAddtional()

        sql = \
            '''
            select * from sales_order_additional
            where id>%s
            '''

        with connections['pg_mg_query'].cursor() as cursor:

            logging.info(sql)
            cursor.execute(sql, [obj_max_entity])

            results = namedtuplefetchall(cursor)

            if results:

                try:
                    with transaction.atomic():
                        for i in range(len(results)):
                            obj = OrderAddtional()
                            obj.mg_id = results[i].id
                            obj.order_entity = results[i].order_entity
                            obj.order_item_entity = results[i].order_item_entity
                            obj.instruction = results[i].instruction
                            obj.mg_created_at = results[i].created_at
                            obj.mg_updated_at = results[i].updated_at

                            obj.save()

                            logging.debug('New Instruction: %s' % obj.instruction)

                except Exception as e:
                    logging.debug("When generating order addtional arise Errors: %s" % e)
            else:
                logging.debug("There is no order addtional can be generated !")

            logging.debug('----------------------------------------')

            # sql = 'select id from oms_orderaddtional where mg_id>' + str(obj_max_entity) + ' group by order_entity'

            # sql = 'select id from oms_orderaddtional where is_used=0' + ' group by order_entity'
            # objs = OrderAddtional.objects.raw(sql)

            objs = OrderAddtional.objects.filter(is_used=False)  # .order_by('-id')

            for obj in objs:

                logging.debug('begin ....')
                logging.debug('----------------------------------------')

                if obj.is_used:
                    logging.debug('obj id[%s] has been syns.' % obj.id)
                    continue

                _order_entity = obj.order_entity
                logging.debug('order_entity: %s' % obj.order_entity)

                try:
                    # order instructions
                    if obj.order_item_entity == 0:
                        logging.debug('order ....')
                        order_insts = objs.filter(order_entity=_order_entity, order_item_entity=0).order_by('-id')
                        if len(order_insts) > 0:
                            order_inst = order_insts[0].instruction
                            logging.debug('new instruction: %s' % order_inst)

                            po = PgOrder.objects.get(base_entity=_order_entity)
                            logging.debug('order number: %s' % po.order_number)
                            po.instruction = order_inst
                            po.is_inst = True
                            po.save()

                        for order_inst in order_insts:
                            logging.debug('setting order_inst to true: %s' % order_inst.id)
                            order_inst.is_used = True
                            order_inst.save()

                    # order items instructions
                    elif obj.order_item_entity != 0:
                        logging.debug('order items ....')
                        order_items_insts = objs.filter(order_entity=_order_entity,
                                                        order_item_entity=obj.order_item_entity).order_by('-id')
                        if len(order_items_insts) > 0:
                            order_items_inst = order_items_insts[0].instruction

                            po = PgOrder.objects.get(base_entity=_order_entity)
                            pgois = PgOrderItem.objects.filter(pg_order_entity=po, item_id=obj.order_item_entity)

                            if len(pgois) > 0:
                                pgoi = pgois[0]
                                logging.debug('order number: %s' % po.order_number)
                                logging.debug('order items: %s' % pgoi.item_id)

                                pgoi.instruction = order_items_inst
                                pgoi.save()

                            for oii in order_items_insts:
                                logging.debug('setting order_inst to true: %s' % oii.id)
                                oii.is_used = True
                                oii.save()
                except Exception as e:
                    logging.debug('exception: %s' % str(e))

                logging.debug('----------------------------------------')
                logging.debug('ending ....')

    def get_pgorder_item_detail(self, _order_number, _item_id):
        logging.debug("order_number: %s" % _order_number)
        logging.debug("item_id: %s" % _item_id)
        poi = PgOrderItem.objects.filter(order_number=_order_number, item_id=_item_id)[0]
        dict_poi = {
            "order_entity": poi.pg_order_entity.base_entity,
            "profile_entity": poi.profile_id,
            "order_item_entity": poi.item_id,
            "profile_prescription_entity": poi.profile_prescription_id,
            "prescription_entity": poi.prescription_id
        }
        rb = response_body()
        rb = self.get_order_image(dict_poi)
        logging.debug('response body: %s' % rb.__dict__)
        try:
            if (rb.code == 0):
                logging.debug(rb.body)
                body = rb.body

                logging.debug('rb.body.image_urls: %s' % body['image_urls'])
                poi.pupils_position = body['pupils_position']
                poi.pupils_position_name = body['pupils_position_name']
                poi.save()

                poi.order_image_urls = json.dumps(body['image_urls'])

        except Exception as e:
            logging.exception('exception: %s' % str(e))

        return poi

    def get_order_image(self, dict_poi):

        rb = response_body()

        req_para = request_parameters()
        req_para.parameters = dict_poi
        req_para = utilities.convert_to_dict(req_para)

        req = json.dumps(req_para)
        logging.debug('req parameters: %s' % req_para)

        requrl = settings.PROFILE_ROOT_URL + settings.PROFILE_ORDER_IMAGE_URL
        headers = {'Content-Type': 'application/json'}

        req = urllib2.Request(url=requrl, data=req, headers=headers)

        try:
            res = urllib2.urlopen(req)
            res_json = json.loads(res.read())

            rb.code = res_json.get('code', -1)
            rb.message = res_json.get('message', '')
            rb.body = res_json.get('body', None)

            return rb

        except Exception as e:
            rb.code = -8000
            rb.message = str(e)
            return rb

    def get_pgorder_item_detail_v3(self, _order_number, _item_id, _product_index=0):
        logging.debug("order_number: %s" % _order_number)
        logging.debug("item_id: %s" % _item_id)
        poi = PgOrderItem.objects.filter(order_number=_order_number, item_id=_item_id, product_index=_product_index)[0]

        dict_param = {
            "order_entity": poi.pg_order_entity.base_entity,
            "profile_entity": poi.profile_id,
            "order_item_entity": poi.item_id,
            "profile_prescription_entity": poi.profile_prescription_id,
            "prescription_entity": poi.prescription_id
        }
        rb = response_body()
        rb = self.get_order_image(dict_param)
        logging.debug(rb)
        try:
            if (rb.code == 0):
                logging.debug(rb.body)
                body = rb.body

                logging.debug('rb.body.image_urls: %s' % body['image_urls'])
                poi.pupils_position = body['pupils_position']
                poi.pupils_position_name = body['pupils_position_name']
                poi.save()

                # poi.order_image_urls = json.dumps(body['image_urls'])
                poi.order_image_urls = body['image_urls']

        except Exception as e:
            logging.exception('exception: %s' % str(e))

        return poi

    # pg order address verified
    def pgorder_address_verified(self, entities):
        ailog = ai_log_control()  # AI操作日志
        entities = json.loads(entities)
        try:
            for entity in entities:

                sql = oms.const.sql_generate_pg_orders + oms.const.sql_generate_pg_orders_spe

                with connections["pg_mg_query"].cursor() as cursor:
                    cursor.execute(sql, [entity])
                    results = namedtuplefetchall(cursor)
                    result = results[0]

                    po = PgOrder.objects.get(order_number=entity)

                    logging.critical('order_number: %s' % entity)

                    updated_at = result.updated_at
                    web_updated_at = po.web_updated_at

                    # if not po.web_updated_at == result.updated_at:
                    po.web_updated_at = result.updated_at
                    po.web_status = result.status

                    po.firstname = result.firstname
                    po.lastname = result.lastname
                    po.postcode = result.postcode
                    po.phone = result.telephone

                    str_street = result.street
                    str_street = str_street.encode('utf-8')
                    sec_str = '\n'
                    arr_street = str_street.split(sec_str)

                    po.street = arr_street[0]
                    if len(arr_street) > 1:
                        po.street2 = arr_street[1]

                    # po.street = result.street
                    po.city = result.city
                    po.region = result.region
                    po.country_id = result.country_id

                    po.customer_name = result.customer_name
                    po.email = result.customer_email

                    po.save()

                    res_address = response_address()
                    res_address.street1 = po.street
                    res_address.street2 = po.street2
                    res_address.city = po.city
                    res_address.state = po.region
                    res_address.zip = po.postcode
                    res_address.phone = po.phone
                    res_address.country = po.country_id
                    res_address.company = "EasyPost"

                    try:
                        res_address = utilities.convert_to_dict(res_address)
                        verifications = self.address_verified(res_address)
                        delivery = verifications.get('delivery', '')
                        success = delivery.get('success', '')

                        if not success == True:
                            po.is_issue_addr = True
                            po.save()
                        else:
                            po.is_issue_addr = False
                            po.save()
                    except Exception as e:
                        pass

                    #检查地址
                    check_flag = self.check_address(po)
                    if check_flag:
                        po.is_issue_addr = True
                        po.save()
                        # return JsonResponse(queryset, safe=False)

            json_data = {}
            json_data['message'] = 'ok'
            json_data = json.dumps(json_data)
            ailog.add('pgorderitem', '',entities[0], '自动下单', 'pgorder_address_verified', '', '', '200',
                      'OK', 'YES', '')
            return HttpResponse(json_data)
        except Exception as e:
            for entity in entities:
                po = PgOrder.objects.get(order_number=entity)
                po.is_issue_addr = True
                po.save()
            ailog.add('pgorderitem', '', entities[0], '自动下单', 'pgorder_address_verified', '', '', '500',
                      'ERROR', 'YES', e)
            logging.critical(str(e))
            return HttpResponse(str(e))

    # public method
    def address_verified(self, res_address):
        resp = 'error'

        req_url = settings.EASYPOST_BASE_URL + settings.EASYPOST_ADDRESS
        logging.debug("req_url==>%s" % req_url)

        http_headers = {
            'Authorization': 'Bearer ' + settings.EASYPOST_API_KEY,
            'Content-Type': 'application/json'
        }

        logging.debug("http_headers==>%s" % http_headers)
        send_data = {
            "verify": ['delivery'],
            "address": res_address
        }

        send_data = json.dumps(send_data)
        logging.debug(send_data)

        try:
            # req = urllib2.Request(url=req_url, data=send_data, headers=http_headers)
            # res = urllib2.urlopen(req)
            # resp = res.read()
            req = requests.post(url=req_url, data=send_data, headers=http_headers)
            resp = req.text
            res_json = json.loads(resp)

            verifications = res_json.get('verifications', '')

            #delivery = verifications.get('delivery', '')
            #success = delivery.get('success', '')
            #logging.debug('verifications: %s' % verifications)
            #logging.debug('success: %s' % success)

            return verifications
        except Exception as e:
            logging.exception(e.message)

    def post_estimate_date(self, request, data):
        logging.debug("----------------------------------------")

        rm = response_message()

        rmjs = {}

        if request:
            str_promised_date = request.POST.get("promised_date", '')  # 推给用户的预计发货时间
            str_targeted_date = request.POST.get("targeted_date", '')
            estimated_date = request.POST.get("estimated_date", '')
            order_number = request.POST.get("order_number", '')
        else:
            str_promised_date = data.get("promised_date", '')  # 推给用户的预计发货时间
            str_targeted_date = data.get("targeted_date", '')
            estimated_date = data.get("estimated_date", '')
            order_number = data.get("order_number", '')

            orderNumber = str(order_number)
            token = self.getToken()
            logging.debug("-------------------gettoken_end---------------------")
            # 比较大小
            targeted_date_format = datetime.datetime.strptime(str_targeted_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            targeted_date = datetime.datetime.strptime(targeted_date_format, "%m/%d/%Y")
            promised_date = datetime.datetime.strptime(str_promised_date, "%m/%d/%Y")
            if targeted_date > promised_date:
                dt = targeted_date + datetime.timedelta(days=3)
                date_section = targeted_date_format + '-' + dt.strftime("%m/%d/%Y")
            else:
                date_section = targeted_date_format + '-' + str_promised_date

            req_url = BASE_URL + SET_TO_INLAB_URL
            logging.debug("req_url==>%s" % req_url)
            logging.debug("token==>%s" % token)
            http_headers = {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            }
            logging.debug("http_headers==>%s" % http_headers)
            send_data = {
                'order_number': orderNumber,
                'promised_ship_content': date_section
            }
            send_data = json.dumps(send_data)
            logging.debug("send_data==>%s" % send_data)
            try:
                req = requests.post(url=req_url, data=send_data, headers=http_headers)
                resp = req.text
                respjs = json.loads(resp)  # 字符串转JSON
                if respjs['code'] == 0:
                    PgOrder.objects.filter(order_number=orderNumber).update(targeted_ship_date=str_targeted_date)
                    rm.error_code = '0'  # 取值
                    rm.error_message = u'操作成功'
                else:
                    rm.error_code = '-1'  # 取值
                    rm.error_message = u'操作失败'
            except Exception as e:
                logging.debug("error==>%s" % e)
                # resp = str(e)
                # resp = 1
                rm.error_code = 1
                rm.error_message = str(e)

        return rm

    def fraud_check(self, po):
        rm = response_message()
        if (po.subtotal == 0 or po.total_paid == 0 or po.shipping_and_handling == 0) \
                and (po.status == 'processing' or po.status == 'pending'):

            if po.subtotal == 0:
                item = 'Subtotal'
            elif po.total_paid == 0:
                item = 'Total Paid'
            else:
                item = 'Shipping and Handling'
            msg = 'Attention please, Pg Order[%s] %s is 0 ....' % (po.order_number, item)

            if '测试' in po.instruction:
                msg += '\nTest Order ,Status not changed'
            elif po.coupon_code:
                if po.coupon_code.upper() == 'PG-INTERNAL':
                    msg += '\nTest Order ,Status not changed'
            else:
                po.status = 'fraud'
                po.save()

            dc = DingdingChat()

            dc.send_text_to_chat('chat72dbc9260ec82f1f871d55ad42e51966', msg)

            rm.code = -8
            rm.message = '%s is 0, please check the order detail' % item
        else:
            rm.code = -9
            rm.message = 'Fraud check not pass'
        return rm

    def add_black(self):
        blacklists = BlackList.objects.filter(is_enabled=True)
        for item in blacklists:
            self.black_set.add(item.email)

    def check_address(self, po):
        try:
            # 检查电话是否合规
            if po.phone == '':
                return True

            str_phone = po.phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
            mrepeat = 0
            for i in range(len(str_phone)):
                if str_phone[i] == str_phone[0]:
                    mrepeat = mrepeat + 1

            if mrepeat == len(str_phone):
                return True

            # 再次检查，如果是加急单，street中包含po box字样则标记为问题地址
            if po.ship_direction in ('EXPRESS', 'CA_EXPRESS'):
                if bool(re.search('^.*box.*$', po.street, re.IGNORECASE)) or bool(
                        re.search('^.*box.*$', po.street2, re.IGNORECASE)):
                    return True
            return False
        except Exception as e:
            return True

class response_body:
    body = None
    code = 0
    message = ''

    def __init__(self):
        self.code = 0
        self.message = ''
        self.body = None


class request_parameters:
    parameters = None

    def __init__(self):
        self.parameters = None


class request_order_image:
    order_entity = 0
    profile_entity = 0
    order_item_entity = 0
    prescription_entity = 0
    profile_prescription_entity = 0

    def __init__(self):
        self.order_entity = 0
        self.profile_entity = 0
        self.order_item_entity = 0
        self.prescription_entity = 0
        self.profile_prescription_entity = 0


class respone_order_image:
    order_entity = 0
    profile_entity = 0
    image_url = ''

    def __init__(self):
        self.order_entity = 0
        self.profile_entity = 0
        self.image_url = ''
