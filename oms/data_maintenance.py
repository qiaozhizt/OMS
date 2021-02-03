# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from models.order_models import *
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from const import *
from views import *
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('oms.is_superuser', login_url='/oms/forbid/')
def generate_pgorders_mig(request):
    begin = begin_entity
    end = end_entity
    with connections['pg_mg_query'].cursor() as cursor:
        # magento 网站复合棱镜功能上线后需要更改
        sql = '''select t0.entity_id,t0.status,t0.increment_id,t0.shipping_name,t0.billing_name,t0.created_at
                                ,t0.billing_address,t0.shipping_address,t0.shipping_information
                                ,t0.payment_method
                                #,(case when (t9.base_subtotal+t9.base_discount_amount>=50) then 1 else 0 end) as is_vip
                                ,(select FORMAT(t0.subtotal,2)) as subtotal
                                ,(select FORMAT(t0.grand_total,2)) as grand_total
                                ,(select FORMAT(t0.total_paid,2)) as total_paid
                                ,(select FORMAT(t0.shipping_and_handling,2)) as shipping_and_handling
                                ,(select FORMAT(t9.base_discount_amount,2)) as base_discount_amount_order
                                ,t9.total_qty_ordered

                                ,t10.email as cusomer_email

                                ,t0.customer_id
                                ,t1.parent_item_id
                                ,t4.attribute_set_id
                                ,t1.product_id
                                ,t9.shipping_method
                                ,t9.shipping_description


                                ,t1.item_id
                                ,t1.sku
                                ,t1.name
                                ,t1.qty_ordered




                                ,(select FORMAT(t1.original_price,2)) as original_price
                                ,(select FORMAT(t1.price,2)) as price
                                ,(select FORMAT(t1.base_discount_amount,2)) as base_discount_amount_item
                                ,(case when (t1.price/t1.qty_ordered>=50) then 1 else 0 end) as is_vip


                                ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='lens_width')
                                and entity_id=t1.product_id)) as lens_width
                                ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='bridge')
                                and entity_id=t1.product_id)) as bridge
                                ,(select value from eav_attribute_option_value where store_id='0' and option_id=(select value from catalog_product_entity_int where store_id='0' and attribute_id = (select attribute_id from eav_attribute where attribute_code='temple_length')
                                and entity_id=t1.product_id)) as temple_length
                                ,t1.additional_data
                                ,t1.profile_id
                                ,t1.profile_prescription_id

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
                                
                                ,0 as rpri1
                                ,0 as lpri1
                                ,'' as rbase1
                                ,'' as lbase1
                                
                                ,t2.radd
                                ,t2.ladd
                                ,t2.exam_date
                                ,t2.expire_date
                                ,t2.renew_months
                                ,t2.updated_at

                                ,t3.firstname
                                ,t3.lastname
                                ,t3.postcode
                                ,t3.street
                                ,t3.city
                                ,t3.region
                                ,t3.country_id


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
                                where (t0.status = 'processing' or t0.status='complete') and
                                t0.entity_id >= %s and  t0.entity_id <= %s'''

        """
        """
        logging.info(sql)
        cursor.execute(sql, [begin, end])
        results = namedtuplefetchall(cursor)

        sql_order_list = '''
        select t0.entity_id
        from sales_order_grid t0
        where (t0.status = 'processing' or t0.status='complete') and
                                t0.entity_id >= %s and  t0.entity_id <= %s
        '''

        cursor.execute(sql_order_list, [begin, end])
        results_order_list = namedtuplefetchall(cursor)

        '''
        index =0

        for i in range(begin, end):
            #logging.debug(i)
            print(i)

        for j in range(len(results)):
            #logging.debug((results[j].entity_id))
            #logging.debug(results[j].increment_id)
            if i==results[j].entity_id:
                #logging.debug("true")
                print("true")
            else:
                #logging.debug("false")
                print("false")


            index=index+1
            #logging.debug(index)
            print(index)

        return HttpResponse("complete.")
        '''
        try:
            with transaction.atomic():

                print(results_order_list)
                for ri in range(len(results_order_list)):
                    i = results_order_list[ri].entity_id

                    logging.debug(i)

                    logging.debug("")
                    logging.debug("")
                    logging.debug("######################################################################")
                    logging.debug("正在处理Entity ID: %s pgorder ...." % i)

                    flag = False
                    po = PgOrder()
                    """生成pgorder"""
                    for r in range(len(results)):
                        if results[r].entity_id == i:
                            flag = True
                            po.order_number = results[r].increment_id
                            logging.debug("Pg Order Number: %s" % po.order_number)
                            po.customer_id = results[r].customer_id

                            po.customer_name = results[r].name
                            po.status = results[r].status
                            po.email = results[r].cusomer_email

                            po.order_date = results[r].created_at

                            po.order_datetime = results[r].created_at

                            po.subtotal = results[r].subtotal
                            po.grand_total = results[r].grand_total
                            if results[r].total_paid <> None:
                                po.total_paid = results[r].total_paid

                            po.shipping_and_handling = results[r].shipping_and_handling
                            po.base_discount_amount_order = results[r].base_discount_amount_order
                            po.total_qty_ordered = Decimal(results[r].total_qty_ordered).quantize(Decimal('0.00'))
                            po.firstname = results[r].firstname
                            po.lastname = results[r].lastname
                            po.postcode = results[r].postcode
                            po.street = results[r].street
                            po.city = results[r].city
                            po.region = results[r].region
                            po.country_id = results[r].country_id
                            po.shipping_method = results[r].shipping_method
                            if results[r].shipping_method == 'express_express':
                                po.ship_direction = 'EXPRESS'
                                po.promised_ship_date = (results[r].created_at + datetime.timedelta(days=8)).strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            elif results[r].shipping_method == 'canada_express_canada_express':
                                pgorderitem.ship_direction = 'CA_EXPRESS'
                                pgorderitem.promised_ship_date = (
                                        results[r].created_at + datetime.timedelta(days=8)).strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            else:
                                po.ship_direction = 'STANDARD'
                                po.promised_ship_date = (results[r].created_at + datetime.timedelta(days=16)).strftime(
                                    "%Y-%m-%d %H:%M:%S")

                            if results[r].country_id == 'CN':
                                po.ship_direction = 'EMPLOYEE'
                                po.promised_ship_date = (results[r].created_at + datetime.timedelta(days=16)).strftime(
                                    "%Y-%m-%d %H:%M:%S")

                            if results[r].is_vip == 1:
                                po.is_vip = True
                            else:
                                po.is_vip = False

                            po.shipping_description = results[r].shipping_description
                            po.save()
                            # logging.debug("--------------po.order_numbre==>%s" % po.order_number)
                            break

                    logging.debug("flag==> " + str(flag))
                    if flag:
                        pois = PgOrderItem.objects.filter(order_number=po.order_number)
                        if len(pois) == 0:
                            '''所有entity_id和i相等的'''
                            relatelist = []
                            '''parent_id == None'''
                            nonelist = []
                            for j in range(len(results)):
                                if i == results[j].entity_id:
                                    relatelist.append(results[j])

                            for k in range(len(relatelist)):
                                if relatelist[k].parent_item_id == None:
                                    nonelist.append(relatelist[k])
                            for y in range(len(nonelist)):
                                logging.debug("正在生成第 %s pgorderitem" % nonelist[y].increment_id)
                                pgorderitem = PgOrderItem()
                                # pgorder.quantity = nonelist[y].quantity
                                if nonelist[y].rsph == None:
                                    pgorderitem.od_sph = 0.00
                                else:
                                    pgorderitem.od_sph = nonelist[y].rsph

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

                                if nonelist[y].rpri == None:
                                    pgorderitem.od_prism = 0.00
                                else:
                                    pgorderitem.od_prism = nonelist[y].rpri

                                if nonelist[y].rbase == None:
                                    pgorderitem.od_base = ''
                                else:
                                    odbase = nonelist[y].rbase
                                    pgorderitem.od_base = odbase.upper()

                                if nonelist[y].rpri1 == None:
                                    pgorderitem.od_prism1 = 0.00
                                else:
                                    pgorderitem.od_prism1 = nonelist[y].rpri1

                                if nonelist[y].rbase1 == None:
                                    pgorderitem.od_base1 = ''
                                else:
                                    odbase1 = nonelist[y].rbase1
                                    pgorderitem.od_base1 = odbase1.upper()

                                if nonelist[y].lpri == None:
                                    pgorderitem.os_prism = 0.00
                                else:
                                    pgorderitem.os_prism = nonelist[y].lpri

                                if nonelist[y].lbase == None:
                                    pgorderitem.os_base = ''
                                else:
                                    osbase = nonelist[y].lbase
                                    pgorderitem.os_base = osbase.upper()

                                if nonelist[y].lpri1 == None:
                                    pgorderitem.os_prism1 = 0.00
                                else:
                                    pgorderitem.os_prism1 = nonelist[y].lpri1

                                if nonelist[y].lbase1 == None:
                                    pgorderitem.os_base1 = ''
                                else:
                                    osbase1 = nonelist[y].lbase1
                                    pgorderitem.os_base1 = osbase1.upper()


                                if nonelist[y].lens_width <> None:
                                    pgorderitem.lens_width = nonelist[y].lens_width
                                logging.debug(nonelist[y].lens_width)

                                if nonelist[y].bridge <> None:
                                    pgorderitem.bridge = nonelist[y].bridge
                                logging.debug(nonelist[y].bridge)

                                if nonelist[y].temple_length <> None:
                                    pgorderitem.temple_length = nonelist[y].temple_length
                                logging.debug(nonelist[y].temple_length)

                                if nonelist[y].lens_width <> None and nonelist[y].bridge <> None and nonelist[
                                    y].temple_length <> None:
                                    pgorderitem.size = nonelist[y].lens_width + '-' + nonelist[y].bridge + '-' + \
                                                       nonelist[y].temple_length
                                    logging.debug(pgorderitem.size)

                                # new
                                pgorderitem.quantity = nonelist[y].qty_ordered
                                if nonelist[y].is_vip == 1:
                                    pgorderitem.is_vip = True
                                else:
                                    pgorderitem.is_vip = False

                                if nonelist[y].use_for <> None:
                                    pgorderitem.used_for = nonelist[y].use_for
                                    logging.debug("use_for==>" + str(nonelist[y].use_for))

                                pgorderitem.shipping_method = nonelist[y].shipping_method
                                logging.debug(nonelist[y].shipping_method)
                                pgorderitem.shipping_description = nonelist[y].shipping_description
                                logging.debug(nonelist[y].shipping_description)

                                if nonelist[y].shipping_method == 'express_express':
                                    pgorderitem.ship_direction = 'EXPRESS'
                                    pgorderitem.promised_ship_date = (
                                        results[r].created_at + datetime.timedelta(days=8)).strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                elif  results[r].shipping_method == 'canada_express_canada_express':
                                    pgorderitem.ship_direction = 'CA_EXPRESS'
                                    pgorderitem.promised_ship_date = (
                                            results[r].created_at + datetime.timedelta(days=8)).strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                else:
                                    pgorderitem.ship_direction = 'STANDARD'
                                    pgorderitem.promised_ship_date = (
                                        results[r].created_at + datetime.timedelta(days=16)).strftime(
                                        "%Y-%m-%d %H:%M:%S")

                                if nonelist[y].country_id == 'CN':
                                    pgorderitem.ship_direction = 'EMPLOYEE'
                                    pgorderitem.promised_ship_date = (
                                        results[r].created_at + datetime.timedelta(days=16)).strftime(
                                        "%Y-%m-%d %H:%M:%S")

                                # city,region
                                pgorderitem.city = nonelist[y].city
                                pgorderitem.region = nonelist[y].region

                                # prescription_type,prescription_nameprescription_id
                                pgorderitem.profile_id = nonelist[y].profile_id
                                pgorderitem.prescription_id = nonelist[y].profile_prescription_id
                                pgorderitem.prescription_name = nonelist[y].prescription_name
                                # pgorderitem.prescription_type = nonelist[y].prescription_type

                                pgorderitem.product_index = y

                                pgorderitem.country = nonelist[y].country_id
                                logging.debug(nonelist[y].country_id)
                                pgorderitem.order_number = nonelist[y].increment_id
                                logging.debug(nonelist[y].increment_id)
                                pgorderitem.order_date = nonelist[y].created_at
                                pgorderitem.order_datetime = nonelist[y].created_at
                                logging.debug(nonelist[y].created_at)
                                if nonelist[y].single_pd == 0:
                                    pgorderitem.is_singgle_pd = False
                                else:
                                    pgorderitem.is_singgle_pd = True

                                pgorderitem.pg_order_entity = po
                                pgorderitem.original_price = nonelist[y].original_price
                                pgorderitem.price = nonelist[y].price
                                pgorderitem.base_discount_amount_item = nonelist[y].base_discount_amount_item

                                relateproduct = []
                                for h in range(len(relatelist)):
                                    if relatelist[h].parent_item_id == nonelist[y].item_id:
                                        relateproduct.append(relatelist[h])
                                for x in range(len(relateproduct)):
                                    if x == 0:
                                        # sku = relateproduct[x].sku
                                        # frame = sku[1:len(sku)]
                                        pgorderitem.frame = relateproduct[x].sku
                                        pgorderitem.name = relateproduct[x].name
                                    elif x == 1:
                                        pgorderitem.lens_sku = relateproduct[x].sku
                                        pgorderitem.lens_name = relateproduct[x].name
                                    elif x >= 2:
                                        if relateproduct[x].attribute_set_id == 10:
                                            pgorderitem.coating_sku = relateproduct[x].sku
                                            pgorderitem.coating_name = relateproduct[x].name
                                        if relateproduct[x].attribute_set_id == 12:
                                            pgorderitem.tint_sku = relateproduct[x].sku
                                            pgorderitem.tint_name = relateproduct[x].name
                                pgorderitem.save()


                        else:

                            '''所有entity_id和i相等的'''
                            relatelist = []
                            '''parent_id == None'''
                            nonelist = []
                            for j in range(len(results)):
                                if i == results[j].entity_id:
                                    relatelist.append(results[j])

                            # logging.debug("relatelist==>%s" % relatelist)

                            for k in range(len(relatelist)):
                                if relatelist[k].parent_item_id == None:
                                    nonelist.append(relatelist[k])
                            for i in range(len(nonelist)):
                                order_number = pois[i].order_number
                                logging.debug("正在维护pgorderitem--> %s" % order_number)
                                pois[i].pg_order_entity = po
                                pois[i].original_price = nonelist[i].original_price
                                pois[i].price = nonelist[i].price
                                pois[i].base_discount_amount_item = nonelist[i].base_discount_amount_item
                                pois[i].save()
                                # logging.debug("-----------------pgorderitem->pg_order_entity==>%s" % po)

                logging.debug("-----------------------success------------------------")
                return HttpResponse("success")
        except Exception as e:
            logging.debug("Error==>%s" % e)
            return HttpResponse(str(e))


@login_required
@permission_required('oms.is_superuser', login_url='/oms/forbid/')
def generate_pgorderitem_mig(request):
    pgois = PgOrderItem.objects.all()
    for pgoi in pgois:
        order_number = pgoi.order_number
        logging.debug("-------------pgorderitem->order_number==>%s" % order_number)
        if pgoi.lab_order_entity <> '' and pgoi.lab_order_entity <> None:
            laborder = pgoi.lab_order_entity
            if laborder.base_entity == '' or laborder.base_entity == None:
                lab_number = laborder.lab_number
                logging.debug("-----------laborder->lab_number==>%s" % lab_number)
                laborder.base_entity = pgoi.id
                laborder.save()
                logging.debug("-----------laborder->base_entity==>%s" % pgoi.id)

    return HttpResponse('All success!')








