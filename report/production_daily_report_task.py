# -*- coding: UTF-8 -*-
import logging
import datetime, time
from django.db import connections, transaction
from report.models import ReportConfig, ReportInfo, ReportInfoLine
from util.db_helper import namedtuplefetchall, dictfetchall
from api.models import DingdingChat


def statistical_report():
    data_list = []
    data_tump = [('NewOrderName', 'NewOrderQty'), ('RequestNotesName', 'RequestNotesQty'),
                 ('WorkOrderName', 'WorkOrderQty'),
                 ('DeliveryName', 'DeliveryQty'), ('ReceivedGlassesName', 'ReceivedGlassesQty'),
                 ('GlassesReturnName', 'GlassesReturnQty'),
                 ('GlassesReturnFrameName', 'GlassesReturnFrameQty'),
                 ('C_GlassesReturnName', 'C_GlassesReturnQty'), ('K_GlassesReturnName', 'K_GlassesReturnQty'),
                 ('GlassesFinalName', 'GlassesFinalQty')]
    try:
        logging.debug('Statistical Report Start')
        rep_config = ReportConfig.objects.get(name='生产日报统计表')
        with connections['default'].cursor() as cursor:
            now = datetime.datetime.now()
            now_date = now.strftime('%Y-%m-%d')
            sql = """SELECT '当日新订单总数' AS NewOrderName,
                                        COUNT(t0.id) AS NewOrderQty ,
                                        '当日出库申请总数' AS RequestNotesName,
                                        (SELECT COUNT(t1.id) AS qty FROM oms_laborder_request_notes t0 
                                                LEFT JOIN oms_laborder_request_notes_line t1 
                                                ON t0.id=t1.lrn_id 
                                                LEFT JOIN oms_laborder t2 
                                                ON t2.lab_number=t1.lab_number 
                                         WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s') 
                                         ORDER BY t1.vendor) AS RequestNotesQty,
                                        '当日作业单总数' AS WorkOrderName,
                                        (SELECT COUNT(t0.id) AS qty FROM oms_construction_voucher t0 
                                                LEFT JOIN oms_laborder t2 
                                                ON t2.lab_number=t0.lab_number 
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s'))  AS WorkOrderQty,
                                        '当日出库总数' AS DeliveryName,
                                        (SELECT COUNT(t0.id) AS qty FROM wms_inventory_delivery t0
                                                LEFT JOIN oms_laborder t2
                                                ON t2.lab_number=t0.lab_number
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s') AND doc_type='AUTO') AS DeliveryQty,
                                        '当日装配完成数' AS ReceivedGlassesName,
                                        (SELECT count(t2.lab_number) AS qty FROM oms_received_glasses t0
                                                LEFT JOIN oms_laborder t2
                                                ON t2.lab_number=t0.lab_number
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s')) AS ReceivedGlassesQty,
                                        '当日成镜返工数' AS GlassesReturnName,
                                        (SELECT COUNT(t0.id) AS qty FROM qc_glasses_return t0 
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s')) AS GlassesReturnQty,

                                        '当日镜架返工数' AS GlassesReturnFrameName,
                                        (SELECT COUNT(t0.id) AS qty FROM qc_glasses_return t0
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s') AND t0.doc_type=2) AS GlassesReturnFrameQty,

                                        '当日库存镜片返工数' AS K_GlassesReturnName,
                                        (SELECT COUNT(t0.id) AS qty FROM qc_glasses_return t0 
                                        LEFT JOIN oms_laborder t1 ON t0.lab_number=t1.lab_number 
                                        LEFT JOIN oms_labproduct t2 ON t1.lens_sku = t2.sku 
                                        WHERE DATE(CONVERT_TZ(t0.created_at ,@@SESSION .time_zone,'+8:00')) = DATE('%s') AND t2.is_rx_lab=FALSE AND t0.doc_type=1) AS K_GlassesReturnQty,
                                        '当日车房镜片返工数' AS C_GlassesReturnName,
                                        (SELECT COUNT(t0.id) AS qty FROM qc_glasses_return t0 
                                        LEFT JOIN oms_laborder t1 ON t0.lab_number=t1.lab_number 
                                        LEFT JOIN oms_labproduct t2 ON t1.lens_sku = t2.sku 
                                        WHERE DATE(CONVERT_TZ(t0.created_at ,@@SESSION .time_zone,'+8:00')) = DATE('%s') AND t2.is_rx_lab=TRUE AND t0.doc_type=1) AS C_GlassesReturnQty,
                                        '当日终检合格数' AS GlassesFinalName, 
                                        (SELECT COUNT(t0.id) AS qty FROM qc_glasses_final_inspection_technique t0 
                                        WHERE DATE(CONVERT_TZ(t0.created_at,@@session.time_zone,'+8:00'))=DATE('%s')) AS GlassesFinalQty 
                                FROM oms_laborder t0 
                                WHERE DATE(CONVERT_TZ(t0.create_at,@@session.time_zone,'+8:00'))=DATE('%s') """ % (
                now_date, now_date, now_date, now_date, now_date, now_date, now_date, now_date, now_date, now_date)
            cursor.execute(sql)
            items = dictfetchall(cursor)

            repinfos = ReportInfo.objects.filter(year=now.year, month=now.month, day=now.day, name=rep_config.name)
            if len(repinfos) == 0:
                logging.debug('Statistical Report 。。。。。。。。。')
                rep_info = ReportInfo()
                rep_info.name = rep_config.name
                rep_info.year = now.year
                rep_info.month = now.month
                rep_info.day = now.day
                rep_info.save()
                for item in items:
                    for keys in data_tump:
                        data_list.append({
                            'name': item[keys[0]],
                            'qty': item[keys[1]]
                        })

                for keys in data_list:
                    rep_info_line = ReportInfoLine()
                    rep_info_line.base_entity = rep_info.id
                    rep_info_line.item = keys['name']
                    rep_info_line.quantity = keys['qty']
                    rep_info_line.save()

                comments = str(rep_config.comments).format(data_list[0]['name'], data_list[0]['qty'],
                                                           data_list[1]['name'], data_list[1]['qty'],
                                                           data_list[2]['name'], data_list[2]['qty'],
                                                           data_list[3]['name'], data_list[3]['qty'],
                                                           data_list[4]['name'], data_list[4]['qty'],
                                                           data_list[5]['name'], data_list[5]['qty'],
                                                           data_list[6]['name'], data_list[6]['qty'],
                                                           data_list[7]['name'], data_list[7]['qty'],
                                                           data_list[8]['name'], data_list[8]['qty'],
                                                           data_list[9]['name'], data_list[9]['qty'],
                                                           )
                rep_info.comments = comments
                rep_info.save()
        logging.debug('Statistical Report End')
    except Exception as e:
        logging.debug(e)


def send_report():
    data_list = []
    try:
        logging.debug('Send Report Start')
        rep_config = ReportConfig.objects.get(name='生产日报统计表')
        now = datetime.datetime.now()
        repinfos = ReportInfo.objects.filter(year=now.year, month=now.month, day=now.day, name=rep_config.name)
        if len(repinfos) > 0:
            repinfo = repinfos[0]
            comments = repinfo.comments
            comments = comments.replace('\r', '')

            # send dingding message to test chat
            ddc = DingdingChat()
            subscribes = rep_config.subscribe.split(',')
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            for subscribe in subscribes:
                ddc.send_text_to_chat(subscribe, "{0}: \n[{1}]\n\n[{2}]".format(rep_config.name, now, comments))

            repinfo.is_send = True
            repinfo.save()

        logging.debug('Send Report End')
    except Exception as e:
        logging.debug(e)
