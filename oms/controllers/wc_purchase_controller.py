# -*- coding: utf-8 -*-

import logging
import datetime
import simplejson as json
import requests
import threading
from oms.models.order_models import laborder_purchase_order_line
from vendor.models import wc_lens, LensSpecmap
from api.controllers.tracking_controllers import tracking_lab_order_controller
from oms.models.order_models import PurchaseOrderRecords


class wc_purchase_controller:

    def run_purchase(self, request, purchase_order_line_entity):
        # 返回参数
        stat_dict = {}
        channel_range_list = None
        assemble_height_range_list = None
        # 获取实体
        lab_order_entity = purchase_order_line_entity.laborder_entity
        lab_number = lab_order_entity.lab_number
        # 获取五彩镜片信息
        act_lens_sku = lab_order_entity.act_lens_sku[2:]
        # 单加硬镜片处理
        if act_lens_sku[-2:] == 'HC':
            act_lens_sku = act_lens_sku[:-2]
        logging.debug(act_lens_sku)
        wc_lens_entitys = wc_lens.objects.filter(lab_lens_sku=act_lens_sku)
        # 渐进镜片处理设计,不包括平顶双光
        if (float(lab_order_entity.od_add) > 0 or float(lab_order_entity.os_add) > 0) and '平顶' not in lab_order_entity.act_lens_name:
            wc_design_product = ''
            lens_specmaps = LensSpecmap.objects.filter(inner_code=lab_order_entity.pal_design_sku, technology_type='DESIGN', active='ACTIVE', vendor='4')
            if len(lens_specmaps) > 0:
                lens_specmap = lens_specmaps[0]
                wc_design_product = lens_specmap.outer_code
            else:
                stat_dict[lab_number] = {'Success': False, 'Message': '未找到该设计'}
                return stat_dict

            logging.debug(wc_design_product)
            wc_lens_entitys = wc_lens_entitys.filter(product_sku=wc_design_product)
        if not wc_lens_entitys.count() == 1:
            stat_dict[lab_number] = {'Success': False, 'Message': '未找到五彩对应的镜片信息'}
            return stat_dict
        wc_lens_entity = wc_lens_entitys[0]

        # 获取此款产品的瞳高和通道列表
        if not wc_lens_entity.product_channel_range == '' and wc_lens_entity.product_channel_range is not None:
            channel_range_str = wc_lens_entity.product_channel_range
            if channel_range_str is not None and not channel_range_str == '':
                channel_range_list = channel_range_str.split('/')
            assemble_height_range_str = wc_lens_entity.product_assemble_height_range
            if assemble_height_range_str is not None and not assemble_height_range_str == '':
                assemble_height_range_list = assemble_height_range_str.split('/')
        logging.debug(wc_lens_entity.code)
        try:
            # 包装数据
            data = self.pack_request_value(lab_order_entity, wc_lens_entity, channel_range_list,
                                           assemble_height_range_list)
            logging.debug('包装完成')
            # 调用接口
            respjs = self.request_web_api(data)
            # 分析结果
            stat_dict = self.analysis_result(request, respjs, purchase_order_line_entity)
            # 存储下单信息
            purchase_order_records = PurchaseOrderRecords.objects.filter(lab_number=lab_number)
            if len(purchase_order_records) > 0:
                pur_order_records = purchase_order_records[0]
                pur_order_records.order_data = data
                pur_order_records.vendor = '4'
                pur_order_records.save()
            else:
                pur_order_records = PurchaseOrderRecords()
                pur_order_records.lab_number = lab_number
                pur_order_records.order_data = data
                pur_order_records.vendor = '4'
                pur_order_records.save()
            # 返回数据
            return stat_dict
        except Exception as e:
            logging.debug(str(e))
            stat_dict[lab_number] = {'Success': False, 'Message': str(e)}
            return stat_dict

    def pack_request_value(self, lab_order_entity, wc_lens_entitys, channel_range_list, assemble_height_range_list):
        today_date = datetime.datetime.now()  # 当前时间
        values = {}  # 请求参数
        # 包装请求参数
        requestdata_part_values = {}
        order_header = {}
        order_header['order_num'] = lab_order_entity.lab_number  # 订单号
        order_header['rq'] = str(today_date)  # datetime  【必填】
        order_header['kf_name'] = '智镜'  # 智镜二级客户名称 string
        if lab_order_entity.tint_name is None:
            order_header['tinting'] = ''
        else:
            order_header['tinting'] = lab_order_entity.tint_name  # 染色 string
        order_header['jblj_yn'] = 0  # bit 不要减薄棱镜
        order_header['remark'] = lab_order_entity.comments  # 备注 string

        frame_info = {}
        frame_info['frame_name'] = lab_order_entity.frame[:-3]  # 镜架代码 string

        if lab_order_entity.frame_type == 'Full Rim':
            frame_type = 'full frame'
        elif lab_order_entity.frame_type == 'Semi Rimless':
            frame_type = 'nylon frame'
        elif lab_order_entity.frame_type == 'Rimless':
            frame_type = 'rimless'
        else:
            frame_type = lab_order_entity.frame_type
        frame_info['frame_type'] = frame_type  # 框型 string   (不给直径则必须给出)
        frame_info['frame_color'] = ''  # 镜架美色 string
        frame_info['ztilt'] = ''  # 镜面角 string
        frame_info['panto'] = ''  # 前倾角 string
        frame_info['bvd'] = ''  # 镜眼距 string
        frame_info['frame_a'] = str(lab_order_entity.lens_width)  # 框宽 string
        frame_info['frame_b'] = str(lab_order_entity.lens_height)  # 框高 string     （与直径相斥，不能同时有值)
        frame_info['frame_ed'] = ''  # 对角线  string
        frame_info['frame_dbl'] = str(lab_order_entity.bridge)  # 鼻梁 string

        right_eye = {}
        right_eye['qty'] = 1  # 有效标志 int    【必填】
        right_eye['lens_code'] = wc_lens_entitys.code  # 产品代码 string    【必填】
        right_eye['index'] = str(wc_lens_entitys.index)  # 折射率 string    【必填】
        right_eye['material'] = wc_lens_entitys.material_sku  # 材料 string    【必填】
        right_eye['products'] = wc_lens_entitys.product_sku  # 产品 string     【必填】
        if lab_order_entity.act_lens_sku[-2:] == 'HC':
            right_eye['treatment'] = 'P-HC'
        elif lab_order_entity.coating_sku is None or lab_order_entity.coating_sku == '':
            right_eye['treatment'] = 'P-HMC'
        elif 'TCO' in lab_order_entity.coating_sku:
            right_eye['treatment'] = 'P-SHMC'
        else:
            right_eye['treatment'] = 'P-'+lab_order_entity.coating_sku  # 镀膜 string    【必填】
        right_eye['zj'] = ''  # 直径 string     (不给框型则必须给出。与框高相斥，不能同时有值)
        if channel_range_list is not None:
            index = -1
            for chan in channel_range_list:
                index += 1
                if chan == '12':
                    break
            right_eye['channel'] = channel_range_list[index]  # 通道 int
            right_eye['min_zph'] = assemble_height_range_list[index]  # 最小装配高度 int
            if lab_order_entity.channel == 'FH15':
                index = -1
                for chan in channel_range_list:
                    index += 1
                    if chan == '11':
                        break
                right_eye['channel'] = channel_range_list[index]
                right_eye['min_zph'] = assemble_height_range_list[index]
        else:
            right_eye['channel'] = ''
            right_eye['min_zph'] = ''
        right_eye['ali_base'] = ''  # BASE基弯  string
        right_eye['sph'] = str(lab_order_entity.od_sph)  # 球镜 string    【必填】
        right_eye['cyl'] = str(lab_order_entity.od_cyl)  # 柱镜 string    【必填】
        right_eye['axe'] = str(lab_order_entity.od_axis)  # 轴位 string    【必填】
        if float(lab_order_entity.od_add) == 0:
            right_eye['add'] = ''
        else:
            right_eye['add'] = str(lab_order_entity.od_add)  # 渐进 string
        # 棱镜------------
        right_pris = {}
        right_pris['UP'] = '90'
        right_pris['DOWN'] = '270'
        right_pris['IN'] = '0'
        right_pris['OUT'] = '180'
        if float(lab_order_entity.od_prism) == 0:
            right_eye['pris1'] = ''
        else:
            right_eye['pris1'] = str(lab_order_entity.od_prism)  # 棱镜1 string
        if lab_order_entity.od_base is None or lab_order_entity.od_base == '':
            right_eye['base1'] = ''  # 底向1 string
            right_eye['base1_fx'] = ''  # 方向1 string
        else:
            right_eye['base1'] = right_pris[lab_order_entity.od_base]  # 底向1 string
            right_eye['base1_fx'] = lab_order_entity.od_base
        if float(lab_order_entity.od_prism1) == 0:
            right_eye['pris2'] = ''
        else :
            right_eye['pris2'] = str(lab_order_entity.od_prism1)  # 棱镜2 string
        if lab_order_entity.od_base1 is None or lab_order_entity.od_base1 == '':
            right_eye['base2'] = ''  # 底向2 string
            right_eye['base2_fx'] = ''
        else:
            right_eye['base2'] = right_pris[lab_order_entity.od_base1]  # 底向2 string
            right_eye['base2_fx'] = lab_order_entity.od_base1  # 方向2 string
        right_eye['dire1'] = ''  # 水平移心 string
        right_eye['dece'] = ''  # 上下移心 string
        right_eye['dire2'] = ''  # 水平移心 string
        # 棱镜------------

        if lab_order_entity.is_singgle_pd:
            right_eye['pd'] = str(float(lab_order_entity.pd) * 0.5)  # 瞳距 string     (不给直径则必须给出)
        else:
            right_eye['pd'] = str(lab_order_entity.od_pd)
        if '平顶' in lab_order_entity.act_lens_name:
            right_eye['ph'] = lab_order_entity.sub_mirrors_height  # 瞳高 string
        else:
            right_eye['ph'] = lab_order_entity.lab_seg_height  # 瞳高 string
        right_eye['ct'] = ''  # 中心厚度 string
        right_eye['et'] = ''  # 边缘厚度 string
        right_eye['lt'] = False  # 美薄 bool
        right_eye['lt_yh'] = False  # 优化 bool
        right_eye['lt_range'] = ''  # 可视范围 string
        right_eye['insert'] = ''  # 上光内移 string

        left_eye = {}
        left_eye['qty'] = 1  # 有效标志 int    【必填】
        left_eye['lens_code'] = wc_lens_entitys.code  # 产品代码 string    【必填】
        left_eye['index'] = str(wc_lens_entitys.index)  # 折射率 string    【必填】
        left_eye['material'] = wc_lens_entitys.material_sku  # 材料 string    【必填】
        left_eye['products'] = wc_lens_entitys.product_sku  # 产品 string     【必填】
        if lab_order_entity.act_lens_sku[-2:] == 'HC':
            left_eye['treatment'] = 'P-HC'
        elif lab_order_entity.coating_sku is None or lab_order_entity.coating_sku == '':
            left_eye['treatment'] = 'P-HMC'
        elif 'TCO' in lab_order_entity.coating_sku:
            left_eye['treatment'] = 'P-SHMC'
        else:
            left_eye['treatment'] = 'P-'+lab_order_entity.coating_sku  # 镀膜 string    【必填】
        left_eye['zj'] = ''  # 直径 string     (不给框型则必须给出。与框高相斥，不能同时有值)
        if channel_range_list is not None:
            index = -1
            for chan in channel_range_list:
                index += 1
                if chan == '12':
                    break
            left_eye['channel'] = channel_range_list[index]  # 通道 int
            left_eye['min_zph'] = assemble_height_range_list[index]  # 最小装配高度 int
            if lab_order_entity.channel == 'FH15':
                index = -1
                for chan in channel_range_list:
                    index += 1
                    if chan == '11':
                        break
                left_eye['channel'] = channel_range_list[index]
                left_eye['min_zph'] = assemble_height_range_list[index]
        else:
            left_eye['channel'] = ''
            left_eye['min_zph'] = ''
        left_eye['ali_base'] = ''  # BASE基弯  string
        left_eye['sph'] = str(lab_order_entity.os_sph)  # 球镜 string    【必填】
        left_eye['cyl'] = str(lab_order_entity.os_cyl)  # 柱镜 string    【必填】
        left_eye['axe'] = str(lab_order_entity.os_axis)  # 轴位 string    【必填】
        if float(lab_order_entity.os_add) == 0:
            left_eye['add'] = ''
        else:
            left_eye['add'] = str(lab_order_entity.os_add)  # 渐进 string
        # 棱镜------------
        left_pris = {}
        left_pris['UP'] = '90'
        left_pris['DOWN'] = '270'
        left_pris['IN'] = '180'
        left_pris['OUT'] = '0'
        if float(lab_order_entity.os_prism) == 0:
            left_eye['pris1'] = ''
        else:
            left_eye['pris1'] = str(lab_order_entity.os_prism)  # 棱镜1 string
        if lab_order_entity.os_base is None or lab_order_entity.os_base == '':
            left_eye['base1'] = ''  # 底向1 string
            left_eye['base1_fx'] = ''  # 方向1 string
        else:
            left_eye['base1'] = left_pris[lab_order_entity.os_base]  # 底向1 string
            left_eye['base1_fx'] = lab_order_entity.os_base
        if float(lab_order_entity.os_prism1)  == 0:
            left_eye['pris2'] = ''
        else:
            left_eye['pris2'] = str(lab_order_entity.os_prism1)  # 棱镜2 string
        if lab_order_entity.os_base1 is None or lab_order_entity.os_base1 == '':
            left_eye['base2'] = ''  # 底向2 string
            left_eye['base2_fx'] = ''
        else:
            left_eye['base2'] = left_pris[lab_order_entity.os_base1]  # 底向2 string
            left_eye['base2_fx'] = lab_order_entity.os_base1  # 方向2 string
        left_eye['dire1'] = ''  # 水平移心 string
        left_eye['dece'] = ''  # 上下移心 string
        left_eye['dire2'] = ''  # 水平移心 string
        # 棱镜------------
        if lab_order_entity.is_singgle_pd:
            left_eye['pd'] = str(float(lab_order_entity.pd) * 0.5)  # 瞳距 string     (不给直径则必须给出)
        else:
            left_eye['pd'] = str(lab_order_entity.os_pd)
        if '平顶' in lab_order_entity.act_lens_name:
            left_eye['ph'] = lab_order_entity.sub_mirrors_height  # 瞳高 string
        else:
            left_eye['ph'] = lab_order_entity.lab_seg_height  # 瞳高 string
        left_eye['ct'] = ''  # 中心厚度 string
        left_eye['et'] = ''  # 边缘厚度 string
        left_eye['lt'] = False  # 美薄 bool
        left_eye['lt_yh'] = False  # 优化 bool
        left_eye['lt_range'] = ''  # 可视范围 string
        left_eye['insert'] = ''  # 上光内移 string

        requestdata_part_values['order_header'] = order_header
        requestdata_part_values['frame_info'] = frame_info
        requestdata_part_values['right_eye'] = right_eye
        requestdata_part_values['left_eye'] = left_eye

        # 请求参数加密
        import hashlib
        str_request_values = json.dumps(requestdata_part_values) + 'B22A94E9-9C0C-4070-81CF-60523FD85DA4'  # 转字符串
        logging.debug('str:' + str_request_values)
        bate_request_values = str_request_values.encode()  # 转二进制
        # MD5加密
        md5_request_values = hashlib.md5(bate_request_values)
        md5_request_values_hex = md5_request_values.hexdigest()
        logging.debug('MD5:' + str(md5_request_values_hex))
        # base64 加密
        import base64
        base64_request_valuse = base64.b64encode(md5_request_values_hex)
        logging.debug('base64:' + base64_request_valuse)

        values['requestdata'] = requestdata_part_values
        values['ebusinessid'] = 511001036
        values['requesttype'] = 1001  # 下单代码
        values['datasign'] = base64_request_valuse
        values['datatype'] = 2

        # 请求参数转JSON
        data = json.dumps(values)
        return data

    def request_web_api(self, data):
        # 定义请求参数
        # url = 'http://106.14.148.226:50009/service/rxorders' # 测试接口
        # url = 'http://106.14.148.226:50009/service/rxapi'
        #url = 'http://106.14.148.226:50009/service/v1/rxapi'
        url = 'http://106.14.148.226:81/service/v1/rxapi'# 更换接口地址2019-11-18
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}

        # 调用接口
        logging.debug('request:' + str(data))
        req = requests.post(url=url, headers=headers, data=data)  # 开始POST请求
        resp = req.text  # 取出响应数据
        respjs = json.loads(resp)  # 解析成JSON

        # 返回响应参数
        logging.debug('Response:%s' % respjs)
        return respjs

    def analysis_result(self, request, respjs, purchase_order_line_entity):
        # 定义返回参数
        stat_dict = {}
        # 获取响应参数
        resultcode = respjs['resultcode']
        success = respjs['success']
        reason = respjs['reason']
        # 开始判断
        if success is True:
            order = respjs['order']
            # 记录五彩单号到采购订单和工厂订单
            purchase_order_line_entity.vendor_order_reference = order['sm_id']
            purchase_order_line_entity.laborder_entity.vendor_order_reference = order['sm_id']
            purchase_order_line_entity.save()
            purchase_order_line_entity.laborder_entity.save()
            # 记录日志
            tloc = tracking_lab_order_controller()
            tloc.tracking(purchase_order_line_entity.laborder_entity, request.user, 'LENS_PURCHASE', '镜片采购',
                          order['sm_id'])
            # 包装消息
            stat_dict[purchase_order_line_entity.lab_number] = {'Success': True, 'Message': '下单成功'}
        else:
            stat_dict[purchase_order_line_entity.lab_number] = {'Success': False, 'Message': reason}

        return stat_dict
