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


class JobStageReport:
    """
    Job Stage Report
    created by guof.
    2020.02.10
    """

    def handle_daily_report(self):
        '''
        Daily Report
        :return:
        '''
        logging.critical('start Daily Report Job Stage ....')
        index = 0
        try:

            logging.debug("start ....")

            msg = self.get_lab_order_status_report()
            self.ding_msg_text(msg)

            file_name = self.get_daily_report_data()
            logging.debug('file name: %s' % file_name)

            now = datetime.datetime.now()
            now_s = now.strftime("%Y-%m-%d")
            txt_body = "每日可加工订单[%s]" % now_s
            self.ding_msg(file_name, txt_body)

            logging.debug("completed ....")

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Daily Report Finance completed ....')

    # Generate Daily Report
    def get_daily_report_data(self):

        file_name = "%s/report/data/job_stage_report/job_stage_report_%s.xlsx"

        now = datetime.datetime.now()
        now_s = now.strftime("%Y-%m-%d")
        file_name = file_name % (settings.RUN_DIR, now_s)
        ew = StyleFrame.ExcelWriter(file_name)

        sqls = self.get_job_stage_sql()
        data = self.get_data(sqls['job_stage_last_7days'])
        self.write2xl(ew, data['titles'], data['items'], "Job Stage 统计报表%s" % sqls['title_parameters'])

        return file_name

    def get_weekly_report_data(self):
        return None

    def get_lab_order_status_report(self):
        sql = '''
            select
            status,
            (case when status='' or status is null then '01.新订单'
            when status='REQUEST_NOTES' then '02.出库申请'
            when status='FRAME_OUTBOUND' then '03.镜架出库'
            when status='PRINT_DATE' then '04.单证打印'
            when status='LENS_OUTBOUND' then '05.镜片出库'
            when status='LENS_REGISTRATION' then '06.来片登记'
            when status='LENS_RETURN' then '07.镜片退货'
            when status='LENS_RECEIVE' then '08.镜片收货'
            when status='ASSEMBLING' then '09.待装配'
            when status='ASSEMBLLED' then '10.装配完成'
            when status='GLASSES_RECEIVE' then '11.成镜收货'
            when status='FINAL_INSPECTION' then '12.终检'
            when status='FINAL_INSPECTION_YES' then '13.终检合格'
            when status='FINAL_INSPECTION_NO' then '14.终检不合格'
            when status='GLASSES_RETURN' then '15.成镜返工'
            when status='COLLECTION' then '16.归集'
            when status='PRE_DELIVERY' then '17.预发货'
            when status='PICKING' then '18.已拣配'
            when status='ORDER_MATCH' then '19.订单配对'
            when status='BOXING' then '20.装箱'
            when status='R2HOLD' then '21.申请暂停'
            when status='R2CANCEL' then '22.申请取消'
            when status='ONHOLD' then '23.暂停'
            when status='CANCELLED' then '24.取消'
            when status='REDO' then '25.重做'
            else status
            end) as status_cn
            ,count(id) as qty
            from oms_laborder
            where date(create_at)>=date('2019.01.01')
            and status not in ('CANCELLED','CLOSED','SHIPPING','DELIVERED')
            group by status_cn
            ;
        '''

        data = self.get_data(sql)
        msgs = []
        msgs.append('Jobs 每日状态报表: \r\n')
        for item in data['items']:
            msg = '%s:%s\n' % (item.status_cn, item.qty)
            msgs.append(msg)

        msgs = ''.join(msgs)

        logging.debug(msgs)
        return msgs

    def get_data(self, sql):
        try:
            with connections['pg_oms_query'].cursor() as cursor:
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

    def get_job_stage_sql(self):
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

        # job stage 报表
        sql = """
            select job_type,stage,year,month,day,hour,
            CONCAT(day,'日',hour,'时') as day_time,
            sum(quantity) as qty from report_job_stage
            where 1=1
            and DATE_SUB(CURDATE(), INTERVAL 7 DAY)<=created_at
            and hour in(7,8,9,10,11,12,13,14,15,16,17,18,19,20,21)
            group by job_type,stage,year,month,day,hour
            order by job_type,CAST(year AS SIGNED),CAST(month AS SIGNED),CAST(day AS SIGNED),stage,CAST(hour AS SIGNED)
            ;
        """

        sql = """
            select year,month,day,hour,
            CONCAT(day,'日',hour,'时') as day_time,
            sum(if(stage='1.外面在做的',quantity,0)) as qty_vd,
            sum(if(stage='2.可以加工的',quantity,0)) as qty_workable,
            sum(if(stage='3.加工完成未发货的',quantity,0)) as qty_finished,
            sum(if(stage='4.我们准备的',quantity,0)) as qty_prepare
            from report_job_stage
            where DATE_SUB(CURDATE(), INTERVAL 7 DAY)<=created_at
            and hour in(7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22)
            group by year,month,day,hour
            order by CAST(year AS SIGNED),CAST(month AS SIGNED),CAST(day AS SIGNED),stage,CAST(hour AS SIGNED)
            ;
        """
        #
        # data['sums_wms_out_lens'] = sql % (date_start, date_end)
        data['job_stage_last_7days'] = sql

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
            sel_chat_id = 'chat90c88f718769057f51ca51311cc1c9bf'  # 陈 张 测试群
            sel_chat_id = 'chat9e26746e4b1020e41bd231a270b43ee3'  # 管理群
            client.chat.send(sel_chat_id, t1)
            client.chat.send(sel_chat_id, t2)

            logging.debug('Ding message has been sent ....')
        except Exception as ex:
            logging.error(str(ex))

    def ding_msg_text(self, txt_body):
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

            t1 = message.TextBody(txt_body)
            # keep touch
            sel_chat_id = 'chat1fa6ffa170a762c040b5f0cc042ade7c'  # keep touch
            sel_chat_id = 'chat596d30e5625ae08b5fd85ebe29b00091'  # IT 周会
            sel_chat_id = 'chat8b63a87cf13980d9ca1e294b946d2c4f'  # 财务群
            sel_chat_id = 'chat90c88f718769057f51ca51311cc1c9bf'  # 陈 张 测试群
            sel_chat_id = 'chat9e26746e4b1020e41bd231a270b43ee3'  # 管理群
            client.chat.send(sel_chat_id, t1)

            logging.debug('Ding message has been sent ....')
        except Exception as ex:
            logging.error(str(ex))
