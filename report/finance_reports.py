# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import logging
import datetime
import time
from datetime import timedelta
from django.db import connections, transaction
from report.models import ReportConfig, ReportInfo, ReportInfoLine
from util.db_helper import namedtuplefetchall, dictfetchall

from django.http import HttpRequest
import pandas as pd
from StyleFrame import StyleFrame, Styler, utils
from dingtalk import SecretClient, AppKeyClient
from dingtalk.model import message
from urllib3 import encode_multipart_formdata
import requests
import simplejson as json

from util.db_helper import *
from util.dict_helper import *
from pg_oms import settings


class FinanceReport:
    """
    Finance Report
    created by guof.
    2019.12.30

    updated by guof.
    2019.12.31

    updated by guof.
    2020.01.05 00:00

    updated by guof.
    2020.02.26
    """

    def handle_daily_report_sales(self):
        '''
        Daily Report
        :return:
        '''
        logging.critical('start Daily Report Finance sales ....')
        index = 0
        try:

            logging.debug("start ....")

            file_name = self.get_daily_report_sales_data()
            logging.debug('file name: %s' % file_name)

            now = datetime.datetime.now()
            now_s = now.strftime("%Y-%m-%d")
            txt_body = "网站每日销售(美国西部时间)通报\n%s" % now_s

            self.ding_msg(file_name, txt_body)

            logging.debug("completed ....")

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Daily Report Finance completed ....')

    def get_daily_report_sales_data(self):
        file_name = "%s/report/data/finance_daily_report/finance_daily_report_sales_%s.xlsx"

        now = datetime.datetime.now()
        now_s = now.strftime("%Y-%m-%d")
        file_name = file_name % (settings.RUN_DIR, now_s)
        ew = StyleFrame.ExcelWriter(file_name)

        items = []
        items.append('Day')
        items.append('总销售额')
        items.append('产品销售')
        items.append('订单数量')
        items.append('眼镜数量')
        items.append('总运费')
        items.append('加急运费')
        items.append('普通运费')
        items.append('平均单价')
        items.append('平均眼镜')
        items.append('车房单')
        items.append('车房占比')
        items.append('车房金额占比')
        items.append('退款')
        items.append('下单日退运费')
        items.append('重做')
        items.append('保险销售')

        data = self.__get_daily_report_sales_data()
        self.write2xl(ew, items, data['items'], "网站每日销售(美国西部时间)通报-%s" % now_s)

        return file_name

    def handle_daily_report(self):
        '''
        Daily Report
        :return:
        '''
        logging.critical('start Daily Report Finance ....')
        index = 0
        try:

            logging.debug("start ....")

            file_name = self.get_daily_report_data()
            logging.debug('file name: %s' % file_name)

            now = datetime.datetime.now()
            now_s = now.strftime("%Y-%m-%d")
            txt_body = "每日财务数据汇总[%s]\r\n1.对账单汇总&清单\n2.镜片出入库汇总&清单\n3.镜架&附件出入库汇总&清单" % now_s
            self.ding_msg(file_name, txt_body)

            logging.debug("completed ....")

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Daily Report Finance completed ....')

    # Generate Daily Report
    def get_daily_report_data(self):

        file_name = "%s/report/data/finance_daily_report/finance_daily_report_%s.xlsx"

        now = datetime.datetime.now()
        now_s = now.strftime("%Y-%m-%d")
        file_name = file_name % (settings.RUN_DIR, now_s)
        ew = StyleFrame.ExcelWriter(file_name)

        sqls = self.get_yesterday_sql()
        sqls['title_parameters'] = ""

        # sql = sqls['sums']
        # logging.debug(sql)
        data = self._get_daily_sums()
        self.write2xl(ew, data['titles'], data['items'], "非自有库存镜片收货汇总%s" % sqls['title_parameters'])

        sql = sqls['detail']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "非自有库存镜片收货明细%s" % sqls['title_parameters'])

        sql = sqls['sums_wms_in_lens']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "自有库存镜片入库汇总-%s" % sqls['title_parameters'])

        sql = sqls['detail_wms_in_lens']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "自有库存镜片入库明细-%s" % sqls['title_parameters'])

        sql = sqls['sums_wms_out_lens']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "自有库存镜片出库汇总-%s" % sqls['title_parameters'])

        sql = sqls['detail_wms_out_lens']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "自有库存镜片出库明细-%s" % sqls['title_parameters'])

        sql = sqls['sums_wms_in']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜架和附件入库汇总-%s" % sqls['title_parameters'])

        sql = sqls['detail_wms_in']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜架和附件入库明细-%s" % sqls['title_parameters'])

        sql = sqls['sums_wms_out']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜架和附件出库汇总-%s" % sqls['title_parameters'])

        sql = sqls['detail_wms_out']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜架和附件出库明细-%s" % sqls['title_parameters'])

        sql = sqls['frame_wms_struct']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜架和附件最新库存量-%s" % sqls['title_parameters'])

        sql = sqls['lens_wms_struct']
        data = self.get_data(sql)
        self.write2xl(ew, data['titles'], data['items'], "镜片最新库存量-%s" % sqls['title_parameters'])

        return file_name

    def get_weekly_report_data(self):
        return None

    def get_data_items(self, sql, conn=None):
        try:
            if not conn:
                conn = connections['pg_oms_query']
            with conn.cursor() as cursor:
                cursor.execute(sql)
                items = namedtuplefetchall(cursor)

            data = {}
            data['items'] = items

            return data
        except Exception as ex:
            logging.error(str(ex))
            return None

    def get_data(self, sql, conn=None):
        try:
            if not conn:
                conn = connections['pg_oms_query']
            with conn.cursor() as cursor:
                cursor.execute(sql)
                titles = self.get_title_list(cursor.description)
                items = namedtuplefetchall(cursor)

            data = {}
            data['titles'] = titles
            data['items'] = items

            return data
        except Exception as ex:
            logging.error(str(ex))
            return None

    def _get_yesterday(self):
        date = {}
        now = datetime.datetime.now()
        yesterday = now - timedelta(days=1)
        logging.debug(yesterday)

        date_str = yesterday.strftime("%Y-%m-%d")

        date_start = date_str + ' 00:00:00'
        date_end = date_str + ' 23:59:59'
        date['date_str'] = date_str
        date['date_start'] = date_start
        date['date_end'] = date_end

        return date

    def get_yesterday_sql(self):
        date = self._get_yesterday()
        date_str = date['date_str']
        date_start = date_str + ' 00:00:00'
        date_end = date_str + ' 23:59:59'

        data = {}
        # 镜片收货汇总
        sql_sums = """
            -- 非自有库存镜片收货汇总
        """
        # sql_sums = sql_sums % (date_start, date_end)
        # data['sums'] = sql_sums

        # logging.debug('sums')

        # 镜片收货明细
        sql_detail = """
        -- 非自有库存镜片收货明细
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day, date_format(convert_tz(
            t0.created_at,'+0:00','+8:00'),'%%H:%%i:%%s') as BJ_Time,
            t1.lab_number, t1.lens_sku, t1.lens_name,t1.act_lens_sku,t1.act_lens_name, t1.coating_sku, t1.coating_name,
            t1.tint_sku, t1.tint_name, t1.pal_design_sku, t1.pal_design_name,
            t1.vendor,t1.workshop, t1.frame, t1.order_type, t1.status, t1.order_number, date_format(convert_tz(
            t1.order_datetime,'+0:00','+8:00'),'%%Y-%%m-%%d') as web_order_day, t1.comments
            from qc_lens_collection t0 left join oms_laborder t1 on t0.laborder_id = t1.id
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t1.status<>'CANCELLED'
            order by day, BJ_Time, t1.vendor,t1.act_lens_sku
        """
        sql_detail = sql_detail % (date_start, date_end)
        data['detail'] = sql_detail
        logging.debug('detail')

        # 镜片入库汇总
        sql_sums_wms_in_lens = """

            -- 自有库存镜片入库汇总

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day,
            t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name, sum(t0.quantity) as qty
            from wms_inventory_receipt_lens t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            group by Day, t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name
            order by Day, t0.warehouse_code, t0.base_sku
            ;
        """

        data['sums_wms_in_lens'] = sql_sums_wms_in_lens % (date_start, date_end)

        # 镜片入库明细
        sql_detail_wms_in_lens = """
            -- 自有库存镜片入库明细

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day, date_format(convert_tz(
            t0.created_at,'+0:00','+8:00'),'%%H:%%i:%%s') as BJ_Time,
            t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name, sku, sph, cyl, t0.quantity,
            case when t0.doc_type = 'ALLOTTED_IN' then '调拨入库' when t0.doc_type='GENERAL_IN' then '一般入库' when t0.doc_type='NP_IN' then '新品入库'
            when t0.doc_type='RP_IN' then '补货入库' when t0.doc_type='REFUNDS_IN' then '订单退货' when t0.doc_type='SAMPLE_IN' then '样品入库'
            when t0.doc_type='STOCK_TAKING' then '盘点调整' else t0.doc_type end as doc_type1,
            t0.doc_number
            from wms_inventory_receipt_lens t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            order by Day, BJ_Time, t0.warehouse_code, t0.base_sku, sku
            ;
        """
        data['detail_wms_in_lens'] = sql_detail_wms_in_lens % (date_start, date_end)

        # 镜片出库汇总
        sql = """
            -- 自有库存镜片出库汇总

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day,
            t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name, sum(t0.quantity) as qty
            from wms_inventory_delivery_lens t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            group by Day, t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name
            order by Day, t0.warehouse_code, t0.base_sku
            ;
        """
        data['sums_wms_out_lens'] = sql % (date_start, date_end)

        # 镜片出库明细
        sql = """
-- 自有库存镜片出库明细
-- 出库表，需要添加 L R 作为左镜片、右镜片
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day, date_format(convert_tz(
            t0.created_at,'+0:00','+8:00'),'%%H:%%i:%%s') as BJ_Time,
            t0.warehouse_code, t0.warehouse_name, t0.base_sku, t0.name, sku, sph, cyl, t0.quantity, lab_number,
            case when t0.doc_type = 'ALLOTTED_OUT' then '调拨出库' when t0.doc_type='AUTO' then '订单出库' when t0.doc_type='FAULTY' then '报损出库'
            when t0.doc_type='GENERAL_OUT' then '一般出库' when t0.doc_type='REFUNDS_OUT' then '订单退货' when t0.doc_type='SAMPLE_OUT' then '样品出库'
            when t0.doc_type='STOCK_TAKING' then '盘点盘亏' else t0.doc_type end as doc_type1,
            t0.doc_number, comments
            from wms_inventory_delivery_lens t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            order by Day, BJ_Time, t0.warehouse_code, t0.base_sku, sku
        """
        data['detail_wms_out_lens'] = sql % (date_start, date_end)

        # 镜架&附件入库汇总
        sql = """
-- 镜架和附件入库汇总
-- 为什么这个表里没有 warehouse_code 和 warehouse_name? 为什么 name 字段也都是空的？

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day,
            t0.warehouse_id, t0.warehouse_code, t0.warehouse_name,
            t0.sku, t0.name, sum(t0.quantity) as qty
            from wms_inventory_receipt t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            group by Day, t0.warehouse_id, t0.sku, t0.name
            order by Day, t0.warehouse_id, t0.sku
            ;
                """
        data['sums_wms_in'] = sql % (date_start, date_end)

        # 镜架&附件入库明细
        sql = """
-- 镜架和附件入库明细

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day, date_format(convert_tz(
            t0.created_at,'+0:00','+8:00'),'%%H:%%i:%%s') as BJ_Time,
            t0.warehouse_id, t0.warehouse_code, t0.warehouse_name,
            t0.sku, t0.name, t0.quantity, t0.lab_number,
            case when t0.doc_type = 'ALLOTTED_IN' then '调拨入库' when t0.doc_type='GENERAL_IN' then '一般入库' when t0.doc_type='NP_IN' then '新品入库'
            when t0.doc_type='RP_IN' then '补货入库' when t0.doc_type='REFUNDS_IN' then '订单退货' when t0.doc_type='SAMPLE_IN' then '样品入库'
            when t0.doc_type='STOCK_TAKING' then '盘点调整' else t0.doc_type end as doc_type1,
            t0.doc_number, t0.comments
            from wms_inventory_receipt t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            order by Day, BJ_Time, t0.warehouse_id, t0.sku
            ;
        """
        data['detail_wms_in'] = sql % (date_start, date_end)

        # 镜架&附件出库汇总
        sql = """
-- 镜架和附件出库汇总

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day,
            t0.warehouse_id, t0.warehouse_code, t0.warehouse_name,
            t0.sku, t0.name, sum(t0.quantity) as qty
            from wms_inventory_delivery t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            group by Day, t0.warehouse_id, t0.sku, t0.name
            order by Day, t0.warehouse_id, t0.sku
            ;
        """
        data['sums_wms_out'] = sql % (date_start, date_end)

        # 镜架&附件出库明细
        sql = """
-- 镜架和附件出库明细

            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as Day, date_format(convert_tz(
            t0.created_at,'+0:00','+8:00'),'%%H:%%i:%%s') as BJ_Time,
            t0.warehouse_id, t0.warehouse_code, t0.warehouse_name,
            t0.sku, t0.name, t0.quantity, t0.lab_number,
            case when t0.doc_type = 'ALLOTTED_OUT' then '调拨出库' when t0.doc_type='AUTO' then '订单出库' when t0.doc_type='FAULTY' then '报损出库'
            when t0.doc_type='GENERAL_OUT' then '一般出库' when t0.doc_type='REFUNDS_OUT' then '订单退货' when t0.doc_type='SAMPLE_OUT' then '样品出库'
            when t0.doc_type='STOCK_TAKING' then '盘点盘亏' else t0.doc_type end as doc_type1,
            t0.doc_number, t0.comments
            from wms_inventory_delivery t0
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00',
            '+0:00')
            order by Day, BJ_Time, t0.warehouse_id, t0.sku
            ;
        """
        data['detail_wms_out'] = sql % (date_start, date_end)

        # 镜架和配件最新库存量
        sql = """
-- 镜架和配件最新库存量

            select case when status='DRAFT' then '未上架' when status='IN_STOCK' then '在售' when status='OUT_OF_STOCK' then '已下架' else status end as status,
            sku, name, quantity,
            date_format(convert_tz(created_at,'+0:00','+8:00'),'%Y-%m-%d') as Created_Date,
            date_format(convert_tz(updated_at,'+0:00','+8:00'),'%Y-%m-%d') as Last_Update
            from wms_inventory_struct
            order by status, sku
            ;
            """
        data['frame_wms_struct'] = sql

        # 镜片最新库存量
        sql = """
-- 镜片最新库存量

            select
            base_sku, sku, name, sph, cyl, diameter, coating, coating_color, quantity,
            date_format(convert_tz(created_at,'+0:00','+8:00'),'%Y-%m-%d') as Created_Date,
            date_format(convert_tz(updated_at,'+0:00','+8:00'),'%Y-%m-%d') as Last_Update
            from wms_inventory_struct_lens
            order by base_sku, sku
            ;
            """
        data['lens_wms_struct'] = sql

        data['title_parameters'] = date_str
        logging.debug('title_parameters')

        return data

    def get_last_week_sql(self):
        pass

    def get_last_month_sql(self):
        pass

    # 根据游标描述获取Title
    def get_title_list(self, cursor_description):
        data_dict = []
        for field in cursor_description:
            data_dict.append(field[0])
        return data_dict

    # 转换列表类型
    def convert_data_type(self, data):
        list_data = []
        for item in data:
            ll = []
            for k in item:
                if type(item[k]) == decimal.Decimal:
                    ll.append(round(float(item[k]), 2))
                else:
                    ll.append(item[k])
            list_data.append(ll)
        return list_data

    def __get_daily_report_sales_data(self):
        sql = """
            select sales.day, revenue, NetPrdRev, orders, glasses,
            net_ship, Exp_fee, Std_fee, Avg_Od, Avg_Gl, FFs, FF_Pct, FF_A_P,
            lpad(concat('$',format(ifnull(refund_total,0),0)),10,' ') as rfd_total, rfd_ship,
            rmk_a, rfw_a
            from (
            SELECT date_format(convert_tz(so.created_at,@@session.time_zone,'-8:00'),'%Y-%m-%d %a') day,
            lpad(concat('$',format(sum(total_paid),0)),10,' ') as revenue,
            lpad(CONCAT('$',FORMAT(sum(if(so.state = 'closed',0,(so.total_paid - ifnull(so.warranty,0)- ifnull(so.shipping_invoiced,0)))),0)),10,' ') as NetPrdRev,
            lpad(concat('$',format(sum(so.warranty),0)),7,' ') as rfw_a,
            lpad(concat('-$',format(ifnull(sum(total_refunded),0),0)),7,' ') as rfd_a,
            lpad(concat('$',format(sum(ifnull(so.shipping_refunded,0)),0)),7,' ') as rfd_ship,
            lpad(concat('$',format(-1*sum(case when (instr(so.coupon_code,'REPLACE')>0) then so.base_discount_invoiced else 0 end),0)), 6, ' ') as rmk_a,
            lpad(concat('$',format(sum(shipping_invoiced - ifnull(so.shipping_refunded,0)),0)),8,' ') as net_ship,
            lpad(concat('$',format(sum(if(shipping_description like 'Express%',(ifnull(p.shipping_amount,0) - ifnull(p.shipping_refunded,0)),0)),0)),8,' ') as Exp_fee,
            lpad(concat('$',format(sum(if(shipping_description like 'Standard%',(ifnull(p.shipping_amount,0) - ifnull(p.shipping_refunded,0)),0)),0)),8,' ') as Std_fee,
            lpad(CONCAT('$',FORMAT( (sum(total_paid) - sum(shipping_invoiced - ifnull(so.shipping_refunded,0)))/count(so.increment_id),2)),6,' ') as Avg_Od,
            lpad(CONCAT('$',FORMAT( (sum(total_paid) - sum(so.warranty) - sum(shipping_invoiced))/sum(total_qty_ordered-ifnull(ng.Non_Gla,0)),2)),6,' ') as Avg_Gl,
            lpad(format(count(increment_id),0),6,' ') as orders,
            lpad(format(sum(total_qty_ordered),0),6,' ') glasses,
            -- lpad(format(sum(total_qty_ordered-ifnull(ng.Non_Gla,0)),0),6,' ') glasses,
            lpad(format(sum(ifnull(lens.ff,0)),0),6,' ') as FFs,
            CONCAT(FORMAT((sum(ifnull(lens.ff,0)) * 100.0)/sum(so.total_qty_ordered-ifnull(ng.Non_Gla,0)),2),'%') as FF_Pct,
            CONCAT(FORMAT((sum(ifnull(lens.ff_a,0)) * 100.0)/sum(lens.tt_a),2),'%') as FF_A_P
            from (
            select * from sales_order
            where state in ('complete','holded','processing','closed')
            and (coupon_code is null or coupon_code != 'PG-INTERNAL')
            and created_at >= convert_tz(now(),'-8:00','-0:00') - interval 1 month
            ) as so left join (
            select so1.entity_id,
            sum(ifnull(soi.qty_refunded,0)) as rfnds,
            sum(ifnull(soi.qty_ordered,0)) as qty,
            sum(if(ifnull(use_for,'SV') = 'PROGRESSIVE',soi.qty_ordered,0)) as PALs,
            sum(if(ifnull(use_for,'SV') != 'PROGRESSIVE',soi.qty_ordered,0)) as Non_PALs,
            sum(if(ifnull(substr(soi.sku,2,1),'1') = '9',soi.qty_ordered,0)) as Rimless
            from sales_order so1, sales_order_item soi, glasses_prescription p
            where so1.entity_id = soi.order_id
            and soi.glasses_prescription_id = p.entity_id
            and soi.product_type = 'configurable'
            and (so1.coupon_code is null or so1.coupon_code != 'PG-INTERNAL')
            and so1.created_at >= convert_tz(now(),'-8:00','-0:00') - interval 1 month
            group by so1.entity_id
            ) as g on so.entity_id = g.entity_id
            left join (
            select so1.entity_id,
            sum(if(left(soi1.sku,1) != 'S' AND left(soi1.sku,2) != 'LS' AND left(soi1.sku,2) != 'SS' AND left(soi1.sku,1) != 'U',soi1.qty_ordered,0)) as ff,
            sum(if(left(soi1.sku,1) != 'S' AND left(soi1.sku,2) != 'LS' AND left(soi1.sku,2) != 'SS' AND left(soi1.sku,1) != 'U',soi1.row_total,0)) as ff_a,
            sum(soi1.row_total) as tt_a
            -- sum(if(soi1.item_id,soi1.qty_ordered,0)) as Non_Gla
            from sales_order as so1
            left join sales_order_item as soi1 on so1.entity_id = soi1.order_id and soi1.product_type = 'virtual'
            left join catalog_product_entity as prod on soi1.sku = prod.sku
            where prod.attribute_set_id = '14'
            and so1.created_at >= convert_tz(now(),'-8:00','-0:00') - interval 1 month
            and (so1.coupon_code is null or so1.coupon_code != 'PG-INTERNAL')
            group by so1.entity_id
            ) as lens on so.entity_id = lens.entity_id
            left join (
            select so1.entity_id,
            sum(if(soi1.item_id,soi1.qty_ordered,0)) as Non_Gla
            from sales_order as so1
            left join sales_order_item as soi1 on so1.entity_id = soi1.order_id and soi1.product_type = 'donation'
            where so1.created_at >= convert_tz(now(),'-8:00','-0:00') - interval 1 month
            and (so1.coupon_code is null or so1.coupon_code != 'PG-INTERNAL')
            group by so1.entity_id
            ) as ng on so.entity_id = ng.entity_id
            left join sales_order_payment as p on so.entity_id = p.parent_id
            and (so.coupon_code is null or so.coupon_code != 'PG-INTERNAL')
            group by day
            ) as sales
            left join (
            select date_format(convert_tz(created_at,@@session.time_zone,'-8:00'),'%Y-%m-%d %a') day,
            sum(grand_total) refund_total from sales_creditmemo
            where created_at >= convert_tz(now(),'-8:00','-0:00') - interval 1 month
            group by day
            ) as sc on sales.day = sc.day
            order by day
            ;
        """

        conn = connections['pg_mg_query']
        data = self.get_data_items(sql, conn)
        return data

    def _get_daily_sums(self):

        date = self._get_yesterday()
        date_str = date['date_str']
        date_start = date_str + ' 00:00:00'
        date_end = date_str + ' 23:59:59'

        sql_sums = """
-- 非自有库存镜片收货汇总
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as day, t1.vendor,
            t1.act_lens_sku as sku, t1.act_lens_name as name1, count(t0.id) as qty
            from qc_lens_collection t0 left join oms_laborder t1 on t0.laborder_id = t1.id
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t1.status<>'CANCELLED'
            group by day, vendor, sku, name1
            order by day, vendor, sku
        """

        data = self.get_data(sql_sums % (date_start, date_end))

        sql_sums = """
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as day, t1.vendor,
            trim(ifnull(nullif(t1.pal_design_sku,''),'无设计')) as sku,
            trim(ifnull(nullif(t1.pal_design_name,''),'无设计')) as name1, count(t0.id) as qty
            from qc_lens_collection t0 left join oms_laborder t1 on t0.laborder_id = t1.id
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t1.status<>'CANCELLED'
            group by day, vendor, sku, name1
            order by day, vendor, sku
        """

        data['items'].extend([])
        items = self.get_data(sql_sums % (date_start, date_end))
        data['items'].extend(items['items'])

        sql_sums = """
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as day, t1.vendor,
            trim(ifnull(nullif(t1.coating_sku,''),'无额外镀膜')) as sku,
            trim(ifnull(nullif(t1.coating_name,''),'无额外镀膜')) as name1, count(t0.id) as qty
            from qc_lens_collection t0 left join oms_laborder t1 on t0.laborder_id = t1.id
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t1.status<>'CANCELLED'
            group by day, vendor, sku, name1
            order by day, vendor, sku
        """

        data['items'].extend([])
        items = self.get_data(sql_sums % (date_start, date_end))
        data['items'].extend(items['items'])

        sql_sums = """
            select date_format(convert_tz(t0.created_at,'+0:00','+8:00'),'%%Y-%%m-%%d') as day, t1.vendor,
            trim(ifnull(nullif(t1.tint_sku,''),'无染色')) as sku,
            trim(ifnull(nullif(t1.tint_name,''),'无染色')) as name1, count(t0.id) as qty
            from qc_lens_collection t0 left join oms_laborder t1 on t0.laborder_id = t1.id
            where t0.created_at >= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t0.created_at <= convert_tz(str_to_date('%s', '%%Y-%%m-%%d %%H:%%i:%%s'),'+8:00','+0:00')
            and t1.status<>'CANCELLED'
            group by day, vendor, sku, name1
            order by day, vendor, sku
            ;
        """

        data['items'].extend([])
        items = self.get_data(sql_sums % (date_start, date_end))
        data['items'].extend(items['items'])

        return data

    # Write to Excel
    def write2xl(self, ew, title_list, data_list, sheet_name):
        logging.debug('method: write2xl')

        logging.debug(title_list)

        df = pd.DataFrame(columns=title_list, data=data_list)
        defaults = {'font': utils.fonts.aharoni, 'font_size': 14}
        list_sf = StyleFrame(df, styler_obj=Styler(**defaults))
        # Style the headers of the table
        header_style = Styler(bold=True, font_size=18)
        list_sf.apply_headers_style(styler_obj=header_style)
        # Change the columns width and the rows height
        list_sf.set_column_width(columns=list_sf.columns, width=30)
        list_sf.set_row_height(rows=list_sf.row_indexes, height=25)

        # list_sf.apply_column_style(cols_to_style=title_list)

        list_sf.to_excel(excel_writer=ew, sheet_name=sheet_name,
                         # Add filters in row 0 to each column.
                         row_to_add_filters=0,
                         # Freeze the columns before column 'A' (=None) and rows above '2' (=1),
                         # columns_and_rows_to_freeze='A2'
                         ).save()

    # Sending Dingdign Message
    def ding_msg(self, file_name, txt_body):
        try:
            logging.debug('Sending ding message ....')

            E_AppKey = 'dingl4ffi9i8c4zl2m41'
            E_AppSecret = 'VZ7L2ue_Fasulcv40CfrmBdLmKLDAgwLWQPDEr1Fd3PlB2TM5caVVjIGpwbYlaRr'
            AgentId = '300734750'
            CorpId = 'ding1876ffde971a32eb'
            client = AppKeyClient(CorpId, E_AppKey, E_AppSecret)  # 新 access_token 获取方式

            headers = {}
            data = {}
            url = 'https://oapi.dingtalk.com/media/upload?access_token=' + client.access_token + '&type=file'
            """
                :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            """
            data['media'] = (file_name, open(r'%s' % file_name, 'rb').read())
            encode_data = encode_multipart_formdata(data)
            data = encode_data[0]
            headers['Content-Type'] = encode_data[1]
            r = requests.post(url, headers=headers, data=data)
            k = json.loads(r.text)

            t1 = message.TextBody(txt_body)
            t2 = message.FileBody(k.get('media_id'))
            # keep touch
            sel_chat_id = 'chat1fa6ffa170a762c040b5f0cc042ade7c'  # keep touch
            sel_chat_id = 'chat596d30e5625ae08b5fd85ebe29b00091'  # IT 周会
            sel_chat_id = 'chat8b63a87cf13980d9ca1e294b946d2c4f'  # 财务群
            client.chat.send(sel_chat_id, t1)
            client.chat.send(sel_chat_id, t2)

            logging.debug('Ding message has been sent ....')
        except Exception as ex:
            logging.error(str(ex))
