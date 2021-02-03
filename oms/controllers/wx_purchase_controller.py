# -*- coding: utf-8 -*-

import logging

from pg_oms.settings import WX_PURCHASE, MG_ED_URL
import simplejson as json
import datetime,time
import urllib2
import requests
import threading
from django.db import transaction
from oms.models.order_models import laborder_purchase_order_line, PurchaseOrderRecords,PgOrderItem
from vendor.models import wx_product_contrast
from vendor.models import lens_order
from django.db.models import Q
from api.controllers.tracking_controllers import tracking_lab_order_controller
from vendor.contollers import lens_contoller
from util.response import response_message as res_msg


# from urlparse import urljoin

class wx_purchase_controller:
    '''
    WX Purchase Controller class
    # param: #
    '''

    # logging.debug(WX_PURCHASE['WX_SERVICE_ACCOUNTS'])
    # logging.debug(WX_PURCHASE['WX_SERVICE_ORDER_ADD'])
    # logging.debug(WX_PURCHASE['WX_SERVICE_ORDER_STATUS_UPDATE'])

    def __init__(self, is_incode=True):
        self.IsInternalCode = is_incode  # 是否使用为伟星内部代码
        self.accounts = 1  # 账套id
        self.ZCode = 'A100311'  # 致镜客户码 固定的 A100311
        self.CustID = '20190308'  # 客户ID 可不填
        self.CustName = 'shenzhenzhijing'  # 客户名称 可不填
        self.m_order_info = {}  # 订单信息
        self.m_lens_info = []  # 镜片信息
        self.account_url = WX_PURCHASE['WX_SERVICE_ACCOUNTS']
        self.purchase_url = WX_PURCHASE['WX_SERVICE_ORDER_ADD']
        self.rm = res_msg()
        self.office_design_list = ('PAL-COMP', 'PAL-OFFICE', 'PAL-NL-OFFICE')
        # 棱镜方向对应
        self.direction = {
            'IN': '内',
            'OUT': '外',
            'UP': '上',
            'DOWN': '下'
        }
        # 膜层的对应
        self.coating_name = {
            '': '绿膜',
            'HMC': '绿膜',
            'TCO': '发水膜',
            'SHMC': '发水膜',
            'HC': '加硬',
            'UC': '基片'
        }
        # 渐进设计对应关系
        self.design = {
            'PAL-REG': '4K',
            'PAL-EA': 'AlphaS35NC',
            'PAL-DRIVE': 'Drive2NC',
            'PAL-SPORT': 'sportthinPALNC',
            'PAL-COMP': 'OFF14',  # 办公渐进 1.3米
            # '无形双光': 'BFREE',
            'PAL-OFFICE': 'OFF14',  # 办公室渐进
            'PAL-NEAR': 'AlphaH25NC',
            'PAL-MOBILE': 'AlphaMobileNC',
            'PAL-PRUM': 'AlphaH45NC',
            'PAL-NL-OFFICE': 'OFF14',  # 办公渐进 4米
            # 'IOT 渐进 Alpha H65': 'AlphaH65NC',
        }
        # 镜架类型对应
        self.frame_type = {
            'Full Rim': '全框',
            'Semi Rimless': '半框',
            'Rimless': '无框',
        }
        # office 渐进的距离 对应
        self.office_type = {
            'PAL-OFFICE': 0.8,
            'PAL-COMP': 1.3,
            'PAL-NL-OFFICE': 4.0
        }

        self.session = requests.session()
        self.headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko)Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36',
            'Accept-Encoding': ', '.join(('gzip', 'deflate')),
            'Connection': 'keep-alive',
            'Host': '183.193.236.122:8866'
        }

    # 获取账套信息 step1
    def get_account(self):
        try:
            '''
            req = urllib2.Request(self.account_url)
            resp = urllib2.urlopen(req)
            response = resp.read()
            res_json = json.loads(response)
            '''
            start = datetime.datetime.now()
            msg = '调用伟星账户接口'
            self.__start_work(msg)
            resp = self.session.get(self.account_url, headers=self.headers, data=json.dumps({}))
            logging.debug(resp.text)
            res_json = json.loads(resp.text)
            logging.debug(res_json)
            self.accounts = res_json.get('Data')[0].get('AccountId')
            logging.debug(self.accounts)
            self.__get_time_delta_seconds(start, msg)
            return res_json.get('Success')

        except Exception as ex:
            return str(ex)

    # 调用下单接口
    def order_add(self):
        if self.accounts != None:
            # 产品信息不能为 NULL
            for item in self.m_lens_info[0]:
                if self.m_lens_info[0][item] == None:
                    self.m_lens_info[0][item] = ''
            # 下单
            try:
                start = datetime.datetime.now()
                msg = '调用伟星下单接口'
                self.__start_work(msg)
                rsp = requests.post(self.purchase_url,
                                    headers=self.headers,
                                    data=json.dumps(self.m_order_info))
                logging.debug(rsp.content)  # 报错的话用content查看
                self.__get_time_delta_seconds(start, msg)
                return rsp.text
            except Exception as e:
                return str('Request "%s" failed...' % self.purchase_url)

        else:
            return 'AccountId is None...'

    # 拼接需要的数据  拼接订单数据失败时 会抛出异常 需要手动捕获异常
    def set_order_info(self, los, lopol):

        del self.m_lens_info[:]  # 清空数组
        dbl = lopol.laborder_entity.size.split('-')

        # 查询产品代码
        wx_code = self.get_sku_by_act(lopol.laborder_entity.act_lens_sku, lopol.laborder_entity.channel,
                                      lopol.laborder_entity.pal_design_sku)
        if wx_code.count() < 1:
            raise Exception('未找到对应产品Code')
        else:
            m_code = wx_code[0].code

        # 加工瞳高处理  瞳高(渐进的)没有  找子镜高度(双光的) 子镜高度没有 按 lens_height/2 + 4 处理(单光的)
        m_seg_height = lopol.laborder_entity.lab_seg_height
        if m_seg_height in ('', None):
            m_seg_height = lopol.laborder_entity.sub_mirrors_height
            if m_seg_height in ('', None):
                m_seg_height = float(lopol.laborder_entity.lens_height) / 2 + 4

        if m_seg_height in ('', None):
            raise Exception('加工瞳高数据异常.')

        # 膜层的处理  目前只有(绿膜和超防水) 如果增加类型 这里也需要修改
        # 2020.01.19 by guof. OMS-589
        m_coating_name = ""
        try:
            logging.debug("准备获取SKU对应关系数据 ....")
            from vendor.models import wx_product_relationship
            wpr = wx_product_relationship.objects.get(sku=lopol.laborder_entity.coating_sku)
            m_coating_name = wpr.wx_name
            logging.debug("从SKU对应关系Model获取的数据 ....[%s]" % m_coating_name)
        except Exception as ex:
            logging.debug(str(ex))
            m_coating_name = ""

        if not m_coating_name:
            m_coating_name = self.coating_name.get('%s' % lopol.laborder_entity.coating_sku)
            if m_coating_name == '':
                raise Exception('未找到对应膜层数据.')

        # 关于自动过到工厂的订单 同样需要一个染色的深度 暂时通过 ‘%’ 判断是否添加了染色深度 没有的话 加上默认值
        def_tint_color = ''
        if not lopol.laborder_entity.tint_sku in ('', None):
            if lopol.laborder_entity.special_handling is not None and '%' not in lopol.laborder_entity.special_handling:
                def_tint_color = '染色85%' if lopol.laborder_entity.tint_sku[:2] == 'RS' else '染色70%'

        # 关于备注增加双面镀膜的处理
        d_coat = ''
        # 只要是染色的产品 备注中要加上'双面镀膜'  偏光的镜片也要加  目前先根据品名去区分
        if '偏光' in lopol.laborder_entity.lens_name:
            d_coat = '双面镀膜;'
        if lopol.laborder_entity.tint_sku not in ('', None):
            d_coat = '双面镀膜;'
        if '库存单光' in lopol.laborder_entity.act_lens_name and lopol.laborder_entity.tint_sku:
            d_coat = '内表面镀膜'

        # 获取采购类型("LENS", "镜片"),("GLASSES", "成镜"),("ASSEMBLED", "装配")
        purchase_type = lopol.purchase_type
        #获取ED
        lab_frame = lopol.laborder_entity.frame
        web_frame = '1' + lab_frame
        rsp = requests.post(MG_ED_URL,
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps({'sku': web_frame}))
        json_data = json.loads(rsp.content)
        if json_data['code'] == 1:
            ed = json_data['product_info']['ed']
        else:
            web_frame = '2' + lab_frame
            rsp_d = requests.post(MG_ED_URL,
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps({'sku': web_frame}))
            json_data_d = json.loads(rsp_d.content)
            if json_data_d['code'] == 1:
                ed = json_data_d['product_info']['ed']
            else:
                lab_number_list = lopol.laborder_entity.lab_number.split("-")
                new_lab_number = "-".join(lab_number_list[:3])
                pgis = PgOrderItem.objects.filter(lab_order_number=new_lab_number)
                if len(pgis) > 0:
                    pgi = pgis[0]
                    rsp_d = requests.post(MG_ED_URL,
                                          headers={'Content-Type': 'application/json'},
                                          data=json.dumps({'sku': pgi.frame}))
                    json_data_d = json.loads(rsp_d.content)
                    if json_data_d['code'] == 1:
                        ed = json_data_d['product_info']['ed']
                    else:
                        raise Exception('请求ED信息失败.')
                else:
                    raise Exception('请求ED信息失败.')

        for lo in los:
            # 判断需要哪些服务
            IsCut = ''  # 是否割边
            IsAssembly = ''  # 是否装配
            if purchase_type == 'GLASSES':
                IsCut = 'Y'  # 是否割边
                IsAssembly = 'Y'  # 是否装配
            else:
                IsCut = 'N'  # 是否割边
                IsAssembly = 'N'  # 是否装配

            self.m_lens_info.append({
                # 'PKind': lopol.get_purchase_type_display(),  # 产品类型 (车房、镜架)
                'PKind': '车房',  # 产品类型 (车房、镜架)
                'IsInternalCode': self.IsInternalCode,  # 是否为伟星产品代码 (TRUE)
                'Code': m_code,  # 产品代码
                'Number': lo.quantity,  # 数量 单位0.5？
                'FSPH': lo.sph,
                'FCYL': lo.cyl,
                'FCADD': lo.add,
                'RL': lo.rl_identification,  # 左右 (R, L)
                'DiaName': '',#lopol.laborder_entity.dia_1,  # 直径
                'Base': '',  # 基弯 与目前系统中的base不同
                'CenterT': '',  # 中心厚度
                'Edge': '',  # 边缘厚度
                'PD': lo.pd,
                'PH': m_seg_height,  # 瞳高
                'Decenter': '',  # 移心
                'Prism': lo.prism,  # 横向棱镜度
                # 'Direction': lo.base,  # 横向棱镜方向
                'Direction': self.direction.get(lo.base),  # 横向棱镜方向 (上下内外)
                'Prism1': lo.prism1,  # 纵向镜度
                'Direction1': self.direction.get(lo.base1),  # 纵向棱镜方向
                'Radian': '',  # 镜架弧度
                'Panto': '',  # 前倾角
                'Distance': '',  # 镜跟距
                'IsCut': IsCut,  # 是否割边 (Y, N)
                'IsAssembly': IsAssembly,  # 是否装配 (Y, N) 目前为 N
                'Channel': '',  # 通道
                'Coating': m_coating_name,  # 膜层
                'ColorType': lopol.get_wx_tint_type,  # 染色类型 (标准, 渐层色)
                'Coloring': '%s; %s; %s' % (
                    lopol.laborder_entity.tint_name, def_tint_color, lopol.laborder_entity.special_handling),  # 染色内容
                'AXIS': lo.axis,
                # 'PSizeA': lopol.laborder_entity.frame[0:4],  # 镜架型号
                # 'PSizeB': lopol.laborder_entity.frame[-3:],  # 镜架色号
                # 'Width': lopol.laborder_entity.lens_width,
                # 'Height': lopol.laborder_entity.lens_height,
                # 'FrameType': self.frame_type.get(lopol.laborder_entity.frame_type, ''),  # 框型
                'ED': ed,
                'DBL': dbl[1] if len(dbl) == 3 else '',
                'Design': self.design.get(lopol.laborder_entity.pal_design_sku),
                'Thin': '老花美薄' if lopol.laborder_entity.special_handling_sku not in ('', None) else '',
                'Elliptical': 0,
                # 除了双光的都要填Primer HC  所以就用是否有子镜高度字段来判断是否为双光镜片
                'Hardened': 'Primer HC' if lopol.laborder_entity.sub_mirrors_height in ('', None) else '',
                'AdjustDistance': self.office_type.get(lopol.laborder_entity.pal_design_sku, 0)
            })
        # 判断框型
        FrameType = self.frame_type.get(lopol.laborder_entity.frame_type),
        if purchase_type == 'LENS':
            FrameType = ''
        self.m_lens_info.append({
            'PKind': '镜架',  # 产品类型 (车房、镜架)
            'IsInternalCode': self.IsInternalCode,  # 是否为伟星产品代码 (TRUE)
            'Code': m_code,  # 产品代码
            'Number': 1,  # 数量 单位0.5？
            # 'FSPH': lo.sph,
            # 'FCYL': lo.cyl,
            # 'FCADD': lo.add,
            # 'RL': lo.rl_identification,  # 左右 (R, L)
            'DiaName': '',#lopol.laborder_entity.dia_1,  # 直径
            'Base': '',  # 基弯 与目前系统中的base不同
            'CenterT': '',  # 中心厚度
            'Edge': '',  # 边缘厚度
            # 'PD': lo.pd,
            # 'PH': m_seg_height,  # 瞳高
            'Decenter': '',  # 移心
            # 'Prism': lo.prism,  # 横向棱镜度
            # 'Direction': lo.base,  # 横向棱镜方向
            # 'Direction': self.direction.get(lo.base, ''),  # 横向棱镜方向 (上下内外)
            # 'Prism1': lo.prism1,  # 纵向镜度
            # 'Direction1': self.direction.get(lo.base, ''),  # 纵向棱镜方向
            'Radian': '',  # 镜架弧度
            'Panto': '',  # 前倾角
            'Distance': '',  # 镜跟距
            # 'IsCut': 'Y',  # 是否割边 (Y, N)
            # 'IsAssembly': 'Y',  # 是否装配 (Y, N) 目前为 N
            'Channel': '',  # 通道
            # 'Coating': m_coating_name,  # 膜层
            # 'ColorType': lopol.get_wx_tint_type,  # 染色类型 (标准, 渐层色)
            # 'Coloring': lopol.get_wx_tint_color,  # 染色内容
            # 'AXIS': lo.axis,
            'PSizeA': lopol.laborder_entity.frame[:-3],  # 镜架型号
            'PSizeB': lopol.laborder_entity.frame[-3:],  # 镜架色号
            'Width': lopol.laborder_entity.lens_width,
            'Height': lopol.laborder_entity.lens_height,
            'FrameType': FrameType,  # 框型
            'ED': ed,
            'DBL': dbl[1] if len(dbl) == 3 else '',
            # 'Design': self.design.get(lopol.laborder_entity.pal_design_sku, ''),
            # 'Thin': '老花美薄' if lopol.laborder_entity.special_handling_sku not in ('', None) else '',
            'Elliptical': 0,
            # 除了双光的都要填Primer HC  所以就用是否有子镜高度字段来判断是否为双光镜片
            # 'Hardened': 'Primer HC' if lopol.laborder_entity.sub_mirrors_height in ('', None) else '',
            # 'AdjustDistance': self.office_type.get(lopol.laborder_entity.pal_design_sku, 0)
        })

        remark = '订单类型:%s;备注:%s;%s;加工瞳高:%s; 装配瞳高:按标准瞳高%s; 加工要求:%s;  设计编码:%s; 设计名称:%s' % (
            lopol.get_purchase_type_display(),
            d_coat,
            lopol.laborder_entity.comments,
            lopol.laborder_entity.lab_seg_height,
            lopol.laborder_entity.assemble_height,
            lopol.laborder_entity.special_handling,
            lopol.laborder_entity.pal_design_sku,
            lopol.laborder_entity.pal_design_name,
        )

        self.m_order_info = {
            'AccountId': self.accounts,  # 账套id
            'ZCode': self.ZCode,  # 客户助记码,用于关联客户
            'CustID': lopol.laborder_entity.profile_id,  # 客户自定义ID
            'CustName': lopol.laborder_entity.profile_name,  # 客户自定义名称
            'Products': self.m_lens_info,  # 产品列表,用于匹配产品和产品参数
            'ORefrenceID': lopol.laborder_entity.lab_number,  # 客户订单号
            # 订单性质(正常订单/内部订单/紧急订单/投诉订单) 目前写死
            'OrderPT': '正常订单' if lopol.laborder_entity.act_ship_direction == 'EXPRESS' else '紧急订单',
            'Express': 'Standard',  # 快运方式
            # 'Remark': remark  # 客户备注
            'Remark': remark  # 客户备注
        }

        #存储下单信息
        purchase_order_records = PurchaseOrderRecords.objects.filter(lab_number=lopol.laborder_entity.lab_number)
        if len(purchase_order_records) > 0:
            pur_order_records = purchase_order_records[0]
            pur_order_records.order_data = json.dumps(self.m_order_info)
            pur_order_records.vendor = '9'
            pur_order_records.save()
        else:
            pur_order_records = PurchaseOrderRecords()
            pur_order_records.lab_number = lopol.laborder_entity.lab_number
            pur_order_records.order_data = json.dumps(self.m_order_info)
            pur_order_records.vendor = '9'
            pur_order_records.save()

    # 通过 oms_wx_product_contrast_models 表查询对应关系
    def get_sku_by_act(self, act_lens_sku, channel, design):
        # 通过 实际镜片 设计 和 通道 来确定单个产品code
        qr_dict = {'act_lens_sku': act_lens_sku}
        # 如果通道不为空添加通道的筛选
        if channel not in ('', None):
            qr_dict['channel'] = channel
        else:  # 通道为空时de情况 镜片为办公类型 渐进片没有选通道 或者 单光
            if design not in ('', None):  # 有设计的镜片 渐进镜片
                if design in self.office_design_list:
                    qr_dict['channel'] = 'OFFICE'  # 办公镜的情况
                else:
                    qr_dict['channel'] = 'FH17'  # 内渐进镜片 默认没填的情况

        return wx_product_contrast.objects.filter(**qr_dict).only('code')

    # 下单流程
    def run_purchase(self, sub_list, request):
        stat_list = {}  # 下单结果集

        lopols = laborder_purchase_order_line.objects.filter(pk__in=sub_list)

        for lopol in lopols:
            # 如果当前订单已经下单 进入下一次循环
            if lopol.is_purchased:
                stat_list[lopol.lab_number] = {'Success': False, 'Message': '该订单已下单'}
                continue

            if lopol.laborder_entity.status not in (
                    'PRINT_DATE', 'LENS_REGISTRATION', 'LENS_RECEIVE', 'ASSEMBLING', 'FRAME_OUTBOUND', 'REQUEST_NOTES'):
                stat_list[lopol.lab_number] = {'Success': False, 'Message': '该状态不能下单'}
                continue

            los = lens_order.objects.filter(lab_number=lopol.lab_number)
            if len(los) == 0:
                stat_list[lopol.lab_number] = {'Success': False, 'Message': '未找到对应lens_order信息'}
                continue

            with transaction.atomic():
                # 拼接镜片信息 & 添加订单 & 获取伟星订单信息   拼接订单数据失败时 会抛出异常 需要手动捕获异常
                try:
                    self.set_order_info(los, lopol)
                except Exception as e:
                    stat_list[lopol.lab_number] = {'Success': False, 'Message': '产品信息拼接失败: %s' % str(e)}
                    continue  # 数据异常直接跳到下一单

                try:
                    order_info = json.loads(self.order_add())
                except Exception as e:
                    stat_list[lopol.lab_number] = {'Success': False, 'Message': '下单失败: %s' % str(e)}
                    continue  # 数据异常直接跳到下一单

                if order_info['Success']:
                    lopol.vendor_order_reference = order_info['Data']
                    lopol.laborder_entity.vendor_order_reference = order_info['Data']
                    lopol.save()
                    lopol.laborder_entity.save()
                else:
                    lopol.comments = order_info['Message']
                    lopol.save()

                # 准备返回数据
                stat_list[lopol.lab_number] = order_info

                # 记录日志 里面加了try
                tloc = tracking_lab_order_controller()
                tloc.tracking(lopol.laborder_entity, request.user, 'LENS_PURCHASE', '镜片采购', order_info['Message'])

        return stat_list

    def get_purchase_list(self, line_id):
        return laborder_purchase_order_line.objects.filter(lpo_id=line_id).values_list('id')

    def __start_work(self, message):
        start = datetime.datetime.now()
        logging.info('////////////////////////////////////////')
        logging.info('----------------------------------------')
        logging.info('%s 开始于: %s ' % (message, start))
        logging.info('----------------------------------------')

    def __get_time_delta_seconds(self, start, message=None):
        end = datetime.datetime.now()
        time_delta = (end - start).seconds
        if message:
            logging.info('----------------------------------------')
            logging.info('%s 结束于: %s ' % (message, end))
            logging.info('%s 耗时: %s 秒' % (message, time_delta))
            logging.info('----------------------------------------')
            logging.info('////////////////////////////////////////')
        return time_delta
