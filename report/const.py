# -*- coding: utf-8 -*-
from __future__ import unicode_literals

SQL_ORDER_REPORT = """
            select %s as report_day,
            /* 取当前日期的订单的总量 */
            (select (select count(t0.id) from oms_pgorder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s )) as web_order,
            (select count(t0.id) from oms_pgorder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s  and t0.is_inlab=False) as undisposed,
            (select sum(t0.quantity) from oms_pgorderitem t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s ) as web_glasses_qty,
            /* 取当前日期的工厂订单的总量 */
            (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number
                in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
                =%s)) as lad_order,
            /* 取当前日期的工厂订单镜片收货的总量 */
            (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number in 
                (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
                =%s) and t0.id in (select laborder_id from qc_lens_collection)) as lens_receive,
            /* 取当前日期的 工厂订单成镜收货的总量 */
            (select count(t0.id) from oms_laborder t0  where t0.is_enabled=True and t0.status<>'CANCELED' and order_number
                in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
                =%s) and t0.id in (select lab_order_entity from oms_received_glasses)) as glasses_recive,
            /* 取当前日期的工厂订单预发货的总量 */
            (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number 
                in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
                =%s) and t0.id in (select lab_order_entity_id from shipment_pre_delivery_line)) as picking
                """

# SQL_ORDER_REPORT =""" set @report_date=%s;
#             /* 取当前日期的订单的总量 */
#             select (select count(t0.id) from oms_pgorder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date ) as web_order,
#             (select count(t0.id) from oms_pgorder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date  and t0.is_inlab=False) as undisposed,
#             (select sum(t0.quantity) from oms_pgorderitem t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date ) as web_glasses_qty,
#             /* 取当前日期的订工厂单的总量 */
#             (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number
#                 in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date)) as lad_order,
#             /* 取当前日期的工厂订单镜片收货的总量 */
#             (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number in
#                 (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date) and t0.id in (select laborder_id from qc_lens_collection)) as lens_receive,
#             /* 取当前日期的 工厂订单成镜收货的总量 */
#             (select count(t0.id) from oms_laborder t0  where t0.is_enabled=True and t0.status<>'CANCELED' and order_number
#                 in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date) and t0.id in (select lab_order_entity from oms_received_glasses)) as glasses_recive,
#             /* 取当前日期的工厂订单预发货的总量 */
#             (select count(t0.id) from oms_laborder t0 where t0.is_enabled=True and t0.status<>'CANCELED' and order_number
#                 in (select t1.order_number from oms_pgorder t1 where date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))
#                 =@report_date) and t0.id in (select lab_order_entity_id from shipment_pre_delivery_line)) as pre_delivery"""


SQL_SHIPPING_SPEED = """
SELECT 
	t0.col_week, t1.sum
FROM (
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 6 WEEK, "%%Y-%%u") AS col_week  union all
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 5 WEEK, "%%Y-%%u") union all
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 4 WEEK, "%%Y-%%u") union all
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 3 WEEK, "%%Y-%%u") union all
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 2 WEEK, "%%Y-%%u") union all
	SELECT DATE_FORMAT(CURDATE() - INTERVAL 1 WEEK, "%%Y-%%u") union all
	SELECT DATE_FORMAT(CURDATE(), "%%Y-%%u")
) t0
LEFT JOIN (
	select
		DATE_FORMAT(create_at,"%%Y-%%u") AS g_date,
		COUNT(*) AS sum
	from
		oms_laborder
	WHERE
		SUBDATE(CURDATE(), INTERVAL 6 WEEK)-DATE_FORMAT(CURDATE(),'%%w') <= DATE(create_at)
		AND lens_sku LIKE '_%s%%'
		AND %s
	GROUP BY g_date ORDER BY g_date
) t1
ON 
	t0.col_week = t1.g_date;
"""

SQL_SHIPPING_SPEED_REPORT_NEW ="""SELECT t0.lab_number, 
                           t0.status, 
                           t0.ship_direction, 
                           t0.vendor, 
                           t0.tint_sku,
                           t1.id AS shipping_id,
                           DATE(t0.create_at) AS created_at,
                           DATE(t1.created_at) AS shipped_date,
                           TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at) AS ship_diff,
                        (CASE WHEN t0.vendor='2' AND (t0.tint_sku='' OR t0.tint_sku IS NULL) THEN
                           (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 48 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN t0.vendor='2' AND t0.tint_sku<>'' AND t0.tint_sku IS NOT NULL THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 96 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN t0.vendor='4' AND (t0.tint_sku='' OR t0.tint_sku IS NULL) THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 96 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN t0.vendor='5' AND (t0.tint_sku='' OR t0.tint_sku IS NULL) THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 48 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN t0.vendor='5' AND t0.tint_sku<>'' AND t0.tint_sku IS NOT NULL THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 96 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN t0.vendor='6' AND (t0.tint_sku='' OR t0.tint_sku IS NULL) THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 48 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 48 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                            WHEN TRIM(t0.vendor)='7' AND (t0.tint_sku IN ('RS-C','RS-H','RS-L','RJ-C','RJ-H','RJ-L')) THEN
                            (CASE WHEN TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)>0 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 96 THEN '1.Qualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 168 THEN '2.Unqualified'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 96 AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)<= 336 THEN '2.Unqualified'
                            WHEN t0.ship_direction='EXPRESS' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 168 THEN '3.Overdue'
                            WHEN t0.ship_direction='STANDARD' AND TIMESTAMPDIFF(HOUR,t0.create_at,t1.created_at)> 336 THEN '3.Overdue'
                            ELSE '4.Unshipped' END)
                        ELSE '4.Unshipped' END) AS shipped_diff_level,
                        t0.quantity
                        FROM oms_laborder t0 LEFT JOIN shipment_pre_delivery_line t1 ON t0.id=t1.lab_order_entity_id
                        WHERE 1=1 
                              AND DATE_SUB(CURDATE(), INTERVAL 30 DAY) <= DATE(t0.create_at)
                              AND t0.status<>'CANCELLED' 
                              AND t0.status<>'ONHOLD' 
                              AND t0.vendor<>'1000'
                 """

SQL_PRODUCTION_REPORT = """
select %s as report_day,
            /* 取当前日期的订单的总量 */
            (select (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s )) as all_order,
            (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s  and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED') as true_order,
            (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s and (t0.status='CANCELLED' or t0.status='CLOSED') ) as unable_order,
            (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s and t0.lab_number like '%%C%%') as reset_order,
            (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s and t0.lab_number like '%%R%%') as customer_order,
            (select count(t0.id) from oms_laborder t0 where date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))
                =%s and t0.lab_number like '%%Z%%') as to_order
"""
SQL_PRODUCTION_DETAIL_REPORT = """
select vendor,count(
CASE WHEN t0.vendor='0'
THEN 1 
WHEN t0.vendor='1' 
THEN 1 
WHEN t0.vendor='2' 
THEN 1 
WHEN t0.vendor='3'
THEN 1 
WHEN t0.vendor='4' 
THEN 1 
WHEN t0.vendor='5'
THEN 1 
WHEN t0.vendor='6'
THEN 1 
WHEN t0.vendor='7'
THEN 1 
WHEN t0.vendor='8'
THEN 1 
WHEN t0.vendor='9' 
THEN 1 
WHEN t0.vendor='10' 
THEN 1 
WHEN t0.vendor='1000'
THEN 1 
END
) all_order,
count(
CASE WHEN t0.vendor='0'
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1 
WHEN t0.vendor='1'
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1 
WHEN t0.vendor='2' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='3' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='4' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='5' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='6' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='7' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='8' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='9' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='10' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
WHEN t0.vendor='1000' 
and t0.is_enabled=True and t0.status<>'CANCELLED' and t0.status<>'CLOSED'
THEN 1
END
) true_order,
count(
CASE WHEN t0.vendor='0' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='1' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='2' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='3' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='4' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='5' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='6' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='7' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='8' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='9' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='10' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
WHEN t0.vendor='1000' 
and  (t0.status='CANCELLED' or t0.status='CLOSED')
THEN 1 
END
) unable_order,
count(
CASE WHEN t0.vendor='0' 
and t0.lab_number like '%%C%%'
THEN 1 
WHEN t0.vendor='1' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='2' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='3' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='4' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='5' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='6' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='7' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='8' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='9' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='10' 
and t0.lab_number like '%%C%%'
THEN 1
WHEN t0.vendor='1000' 
and t0.lab_number like '%%C%%'
THEN 1
END
) reset_order,
count(
CASE WHEN t0.vendor='0' 
and t0.lab_number like '%%R%%'
THEN 1 
WHEN t0.vendor='1' 
and t0.lab_number like '%%R%%'
THEN 1 
 WHEN t0.vendor='2' 
and t0.lab_number like '%%R%%'
THEN 1 
WHEN t0.vendor='3' 
and t0.lab_number like '%%R%%'
THEN 1
 WHEN t0.vendor='4' 
and t0.lab_number like '%%R%%'
THEN 1 
WHEN t0.vendor='5'  
and t0.lab_number like '%%R%%'
THEN 1
 WHEN t0.vendor='6' 
and t0.lab_number like '%%R%%'
THEN 1 
WHEN t0.vendor='7' 
and t0.lab_number like '%%R%%'
THEN 1
WHEN t0.vendor='8' 
and t0.lab_number like '%%R%%'
THEN 1
WHEN t0.vendor='9' 
and t0.lab_number like '%%R%%'
THEN 1
WHEN t0.vendor='10' 
and t0.lab_number like '%%R%%'
THEN 1
WHEN t0.vendor='1000' 
and t0.lab_number like '%%R%%'
THEN 1
END
) customer_order,
count(
CASE WHEN t0.vendor='0' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='1' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='2' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='3' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='4' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='5' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='6' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='7' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='8' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='9' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='10' 
and t0.lab_number like '%%Z%%'
THEN 1 
WHEN t0.vendor='1000' 
and t0.lab_number like '%%Z%%'
THEN 1 
END
) to_order
from oms_laborder t0 
where  date(convert_tz(t0.create_at,@@session.time_zone,'+8:00'))=%s
group by t0.vendor 
"""

SQL_PRODUCTION_RETURN_REPORT = """
SELECT count(0) return_order,vendor FROM qc_glasses_return t0
LEFT JOIN oms_laborder t1
ON t1.lab_number=t0.lab_number and t1.is_enabled=True and t1.status<>'CANCELLED' and t1.status<>'CLOSED'
and  date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))=%s
GROUP BY t1.vendor
"""
SQL_GLASS_RETURN_REPORT="""
SELECT t1.vendor,t1.workshop,t0.reason,t1.lab_number,t1.create_at,t1.`status` FROM qc_glasses_return t0,oms_laborder t1
where t1.lab_number=t0.lab_number 
and  date(convert_tz(t1.create_at,@@session.time_zone,'+8:00'))=%s
and t1.is_enabled=True and t1.status<>'CANCELLED' and t1.status<>'CLOSED'
and t1.vendor=%s
"""

SQL_FLOW_REPORT ="""SELECT t0.lab_number,t0.act_ship_direction,
                              t0.vendor,t0.workshop,t0.frame,
                              t0.frame_type,t0.quantity,t0.act_lens_name,
							  IF(ABS(t0.os_cyl)>2 or ABS(t0.od_cyl)>2,"TRUE","FALSE") AS is_cyl_high,
							  IF(t3.is_rx_lab=TRUE,"C","K") AS lens_type,
                              t0.status,t0.tint_name,t0.order_date,
                              CONVERT_TZ(t0.create_at,'+0:00','+8:00') AS lab_create_at,
                              CONVERT_TZ(t0.update_at,'+0:00','+8:00') AS lab_update_at,
                              CONVERT_TZ(t0.estimated_date,'+0:00','+8:00') AS lab_estimated_date,
                              CONVERT_TZ(t1.created_at,'+0:00','+8:00') AS ready_created_at,
                              CONVERT_TZ(t2.created_at,'+0:00','+8:00') AS pre_created_at,
                              IF(t0.status NOT in ('PRE_DELIVERY', 'PICKING', 'ORDER_MATCH', 'BOXING', 'SHIPPING', 'DELIVERED'),TIMESTAMPDIFF(DAY,CONVERT_TZ(t0.create_at,'+0:00','+8:00'),NOW()),TIMESTAMPDIFF(DAY,CONVERT_TZ(t0.create_at,'+0:00','+8:00'),CONVERT_TZ(t2.created_at,'+0:00','+8:00'))) AS days_of_production,
                              TIMESTAMPDIFF(HOUR,CONVERT_TZ(t0.create_at,'+0:00','+8:00'),CONVERT_TZ(t1.created_at,'+0:00','+8:00')) as diff_ready_hour,
                              TIMESTAMPDIFF(HOUR,CONVERT_TZ(t0.create_at,'+0:00','+8:00'),CONVERT_TZ(t2.created_at,'+0:00','+8:00')) as diff_pre_hour
                        FROM oms_laborder AS t0 
                        LEFT JOIN qc_lens_collection AS t1 
                             ON t0.lab_number=t1.lab_number 
                        LEFT JOIN shipment_received_glasses AS t2 
                             ON t0.lab_number=t2.lab_number 
						LEFT JOIN oms_labproduct AS t3
							 ON t0.lens_sku=t3.sku
                        WHERE t0.status not in ('CLOSED', 'CANCELLED', 'R2CANCEL') 
                             and (date(CONVERT_TZ(t0.create_at,'+0:00','+8:00'))='%s' OR CONVERT_TZ(t0.create_at,'+0:00','+8:00') BETWEEN '%s' AND '%s')"""

SQL_PGORDER_COUPON_REPORT = """SELECT t0.order_number,
               t1.lab_number,
               t0.coupon_code,
               t0.warranty,
               CONVERT_TZ(t0.create_at,'+0:00','+8:00') as create_at 
        FROM oms_pgorder AS t0 
             LEFT JOIN oms_laborder AS t1 
             ON t0.order_number=t1.order_number 
        WHERE t0.coupon_code <>'' and date(t0.create_at)>'2019-01-01'  AND (date(CONVERT_TZ(t0.create_at, '+0:00', '+8:00'))='%s' OR CONVERT_TZ(t0.create_at, '+0:00', '+8:00')
BETWEEN '%s' AND '%s') """


VD9_PURCHASE_DIFF_SQL = """SELECT
                          t0.order_number AS lab_number,
                          t3.vendor AS vendor,
                          t0.status_value AS status_value,
                          t0.reference_code AS reference_code,
                          CONVERT_TZ(t0.created_at,"+00:00",'+8:00') AS vender_created_at,
                          CONVERT_TZ(t3.created_at,"+00:00",'+8:00') AS purchase_created_at,
                          TIMESTAMPDIFF(HOUR, CONVERT_TZ(t3.created_at,"+00:00",'+8:00'), CONVERT_TZ(t0.created_at,"+00:00",'+8:00')) AS diff_hour
                      FROM
                         vendor_wxorderstatus AS t0
                      LEFT JOIN (
                                SELECT
                                    t1.vendor,
                                    t2.lab_number,
                                    t2.lpo_id,
                                    t2.created_at
                                FROM
                                    oms_laborder_purchase_order AS t1
                                LEFT JOIN oms_laborder_purchase_order_line AS t2 ON t1.id = t2.lpo_id WHERE t1.vendor='9') AS t3
                      ON t0.order_number = t3.lab_number WHERE t0.status_value = '订单完成' AND (date(CONVERT_TZ(t3.created_at,'+0:00','+8:00'))='%s' OR CONVERT_TZ(t3.created_at,'+0:00','+8:00') BETWEEN '%s' AND '%s') ORDER BY t3.lpo_id DESC
"""


VD4_PURCHASE_DIFF_SQL = """SELECT
                          t0.order_number AS lab_number,
                          t3.vendor AS vendor,
                          t0.status_value AS status_value,
                          t0.reference_code AS reference_code,
                          CONVERT_TZ(t0.created_at,"+00:00",'+8:00') AS vender_created_at,
                          CONVERT_TZ(t3.created_at,"+00:00",'+8:00') AS purchase_created_at,
                          TIMESTAMPDIFF(HOUR, CONVERT_TZ(t3.created_at,"+00:00",'+8:00'), CONVERT_TZ(t0.created_at,"+00:00",'+8:00')) AS diff_hour
                      FROM
                         vendor_wc_order_status AS t0
                      LEFT JOIN (
                                SELECT
                                    t1.vendor,
                                    t2.lab_number,
                                    t2.lpo_id,
                                    t2.created_at
                                FROM
                                    oms_laborder_purchase_order AS t1
                                LEFT JOIN oms_laborder_purchase_order_line AS t2 ON t1.id = t2.lpo_id WHERE t1.vendor='4') AS t3
                      ON t0.order_number = t3.lab_number WHERE t0.status_value in ('总检', '待发货') AND (date(CONVERT_TZ(t3.created_at,'+0:00','+8:00'))='%s' OR CONVERT_TZ(t3.created_at,'+0:00','+8:00') BETWEEN '%s' AND '%s') ORDER BY t3.lpo_id DESC"""

ARRIVAL_TIME_DIFF_SQL = """SELECT
                    t0.order_number AS lab_number,
                    t0.status_value AS status_value,
                    CONVERT_TZ(t0.created_at,"+00:00",'+8:00') AS z_created_at,
                    CONVERT_TZ(t1.created_at,"+00:00",'+8:00') AS l_created_at,
                    t1.`status`,
                    TIMESTAMPDIFF(HOUR, CONVERT_TZ(t0.created_at,"+00:00",'+8:00'), CONVERT_TZ(t1.created_at,"+00:00",'+8:00')) AS diff_hour
                FROM
                    vendor_wc_order_status AS t0
                LEFT JOIN (SELECT
                    t2.id AS id,
                    t2.lab_number AS lab_number,
                    t2.created_at AS created_at,
                    t3.`status` AS `status`
                FROM
                	qc_lens_registration AS t2 LEFT JOIN oms_laborder AS t3 ON t2.lab_number = t3.lab_number
                WHERE
                    t2.created_at IN (
                        SELECT
                            max(created_at)
                        FROM
                            qc_lens_registration
                        GROUP BY
                            lab_number
                    )) AS t1 ON t0.order_number = t1.lab_number
                WHERE
	                t0.status_value in ('待发货','总检')
                    AND TIMESTAMPDIFF(HOUR, CONVERT_TZ(t0.created_at,"+00:00",'+8:00'), CONVERT_TZ(t1.created_at,"+00:00",'+8:00'))>14 ORDER BY CONVERT_TZ(t1.created_at,"+00:00",'+8:00') DESC"""


DOCTOR_LAB_SQL = """SELECT
	t2.id AS id,
	t2.order_number AS order_number,
	t2.lab_number AS lab_number,
	t2.`status` AS `status`,
	t2.act_ship_direction,
	t2.frame,
	t2.quantity,
	t2.lens_sku,
	t2.lens_name,
	t2.act_lens_sku,
	t2.act_lens_name,
	t2.order_datetime as order_datetime,
    t2.pg_create_at as pg_create_at,
	t2.create_at,
	TIMESTAMPDIFF(HOUR, pg_create_at, t2.create_at) AS pre_diff,
	convert_tz(t3.created_at ,"+00:00",'+8:00') AS qc_create_at,
	TIMESTAMPDIFF(HOUR, t2.create_at, convert_tz(t3.created_at ,"+00:00",'+8:00')) AS qc_diff,
	convert_tz(t4.created_at ,"+00:00",'+8:00') AS ship_create_at,
	TIMESTAMPDIFF(HOUR, t2.create_at, convert_tz(t4.created_at ,"+00:00",'+8:00')) AS ship_diff,
	t2.delivered_at
FROM
	(
		SELECT
			convert_tz(
				t0.order_datetime ,"+00:00",
				'+8:00'
			) AS order_datetime,
			convert_tz(
				t0.create_at ,"+00:00",
				'+8:00'
			) AS pg_create_at,
			t1.id,
			t1.order_number,
			t1.lab_number,
			t1.`status`,
			t1.act_ship_direction,
			t1.frame,
			t1.quantity,
			t1.lens_sku,
			t1.lens_name,
			t1.act_lens_sku,
			t1.act_lens_name,
			convert_tz(
				t1.create_at ,"+00:00",
				'+8:00'
			) AS create_at,
			convert_tz(
				t1.delivered_at ,"+00:00",
				'+8:00'
			) AS delivered_at
		FROM
			oms_pgorder AS t0
		LEFT JOIN oms_laborder AS t1 ON t0.order_number = t1.order_number
		WHERE
			t0.email = 'RutlandEye@live.com'
		AND (
			date(
				CONVERT_TZ(
					t1.create_at,
					'+0:00',
					'+8:00'
				)
			) = '%s'
			OR CONVERT_TZ(
				t1.create_at,
				'+0:00',
				'+8:00'
			) BETWEEN '%s'
			AND '%s'
		)
		ORDER BY
			t0.id DESC
	) AS t2
LEFT JOIN qc_glasses_final_inspection_technique AS t3 ON t2.lab_number = t3.lab_number
LEFT JOIN shipment_pre_delivery_line AS t4 ON t2.id = t4.lab_order_entity_id"""
