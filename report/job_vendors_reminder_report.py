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
from api.models import DingdingChat


class JobVendorsReminder:
    """
    Job Vendors Reminder
    created by guof.
    2020.02.23
    """

    def handle_daily_report(self):
        '''
        Daily Report
        :return:
        '''
        logging.critical('start Daily Report Job Vendors ....')
        index = 0
        try:

            logging.debug("start ....")

            vendors = (
                ('4', 'chat15c992663328870f5d3ccd7042f19eaa', '五彩'),  # 五彩
                ('9', 'chat13c19ee10b14857d48fcaa4c784488cf', '伟星'),  # 伟星
                ('10', 'chat5b02ae31b3003dfee992706d213ebc24', '伟星(现片)'),  # 伟星

                ('3', 'chatbcc0b5808e32fd805dc567af60f0eccd', 'VD3'),  # VD3
                ('7', 'chat98d57b589b287b3b9166a8a394a942c8', '斌晴'),  # 斌晴
                ('11', 'chatcd7b193edf69a22e1439bc68c72a373b', '明月'), # 明月
            )

            dc_in = DingdingChat()
            for vendor in vendors:
                print vendor

                vd = vendor[0]
                chat_id = vendor[1]
                vendor_name = vendor[2]

                data = self.get_report_summary(vd)
                msgs = []
                msgs.append('%s-%s\n' % (vd, vendor_name))
                msgs.append(data)
                msg = ''.join(msgs)
                dc_in.send_text_to_chat('chat119dc6fa7e72953b2de2108adec981fa', msg)  # 总览

                data = self.get_report(vd)
                msgs = []
                msgs.append('%s-%s\n' % (vd, vendor_name))
                msgs.append(data)
                msg = ''.join(msgs)
                dc_in.send_text_to_chat('chatdb33e92b128affdb7667ab4d059c5379', msg)  # 明细

                # logging.debug(data)

                time.sleep(2)

            dc = DingdingChat()
            dc.appkey = 'dingw0gynzvm6pzvfcuk'
            dc.appsecret = 'Dyq6Ia7hezzccDO6zDKTBeTXzvSiMZUdYzkl4kgeErSFjYQxdknW-9oJPNKpGmnV'
            for vendor in vendors:
                print vendor
                vd = vendor[0]
                chat_id = vendor[1]

                data = self.get_report_summary(vd)
                dc.send_text_to_chat(chat_id, data)

                data = self.get_report(vd)
                dc.send_text_to_chat(chat_id, data)
                # logging.debug(data)

                time.sleep(2)

            logging.debug("completed ....")

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Daily Report Finance completed ....')

    def get_weekly_report_data(self):
        return None

    def get_report_summary(self, vendor):
        sql = '''
            select
            t0.vendor
            ,sum(if(datediff(utc_date(),t1.created_at)>7,t0.quantity,0)) as overdue_7
            ,sum(if(datediff(utc_date(),t1.created_at)>5 and datediff(utc_date(),t1.created_at)<=7,t0.quantity,0)) as overdue_5
            ,sum(if(datediff(utc_date(),t1.created_at)>4 and datediff(utc_date(),t1.created_at)<=5,t0.quantity,0)) as overdue_4
            ,sum(if(datediff(utc_date(),t1.created_at)>3 and datediff(utc_date(),t1.created_at)<=4,t0.quantity,0)) as overdue_3
            ,sum(if(datediff(utc_date(),t1.created_at)>2 and datediff(utc_date(),t1.created_at)<=3,t0.quantity,0)) as overdue_2
            from oms_laborder t0
            left join oms_laborder_purchase_order_line t1 on t1.laborder_entity_id = t0.id
            where 1=1
            and t0.status in ('REQUEST_NOTES','FRAME_OUTBOUND','PRINT_DATE','LENS_RETURN','GLASSES_RETURN')
            and datediff(utc_date(),t1.created_at)>2
            and vendor='%s'
            group by t0.vendor
            ;
        '''

        sql = sql % vendor

        logging.debug(sql)

        data = self.__get_data(sql)

        msgs = []
        msgs.append('Jobs Overdue Summary: \n')
        msgs.append('----------------------------------------\r\n')

        if len(data['items']) > 0:
            item = data['items'][0]
            msg = '超7天: %s\n' % item.overdue_7
            msgs.append(msg)

            msg = '超5天: %s\n' % item.overdue_5
            msgs.append(msg)

            msg = '超4天: %s\n' % item.overdue_4
            msgs.append(msg)

            msg = '超3天: %s\n' % item.overdue_3
            msgs.append(msg)

            msg = '超2天: %s\n' % item.overdue_2
            msgs.append(msg)
        else:
            msg = '今天无超期2天以上的订单!'
            msgs.append(msg)

        msgs = ''.join(msgs)

        logging.debug(len(msgs))

        if len(msgs) > 5000:
            msgs = '%s%s' % (msgs[:4997], '...')

        # logging.debug(msgs)
        return msgs

    def get_report(self, vendor):
        sql = '''
            /*
             每日统计各vd超期订单 并钉钉发送
            */
            select t0.id
            ,t0.lab_number
            ,t0.frame
            ,t0.act_lens_name
            ,date(convert_tz(t0.create_at,@@session.time_zone,'+8:00')) as job_created_at
            ,date(convert_tz(t1.created_at,@@session.time_zone,'+8:00')) as po_created_at
            ,DATE_FORMAT(convert_tz(utc_date(),@@session.time_zone,'+8:00'),'%%Y-%%m-%%d') as report_created_at
            ,datediff(utc_date(),t1.created_at) as diff
            ,t0.vendor
            from oms_laborder t0
            left join oms_laborder_purchase_order_line t1 on t1.laborder_entity_id = t0.id
            where 1=1
            and t0.status in ('REQUEST_NOTES','FRAME_OUTBOUND','PRINT_DATE','LENS_RETURN','GLASSES_RETURN')
            and datediff(utc_date(),t1.created_at)>2
            and vendor='%s'
            order by diff desc
            limit 100
            ;
        '''

        sql = sql % vendor

        logging.debug(sql)

        data = self.__get_data(sql)

        msgs = []
        msgs.append('Jobs Overdue List[TOP 100]: \n')
        msgs.append('----------------------------------------\r\n')
        for item in data['items']:
            msg = '%s: %s天 (下单:%s)\n' % (item.lab_number, item.diff, item.po_created_at)
            msgs.append(msg)

        msgs = ''.join(msgs)

        logging.debug(len(msgs))

        if len(msgs) > 5000:
            msgs = '%s%s' % (msgs[:4997], '...')

        # logging.debug(msgs)
        return msgs

    def __get_data(self, sql):
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

        data = self.__get_data(sql_sums % (date_start, date_end))

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
            client.chat.send(sel_chat_id, t1)
            client.chat.send(sel_chat_id, t2)
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
