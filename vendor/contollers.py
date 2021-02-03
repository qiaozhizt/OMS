# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

# from urllib import request, parse
# import urllib.request
# from json import *

from util.response import response_message
from .models import *
from util.db_helper import *
from util.dict_helper import *
from util.response import *
from util.format_helper import *

from oms.models.order_models import LabOrder,PgOrderItem
from oms.models.product_models import PgProduct, LabProduct
from wms.models import lens_extend

from enum import Enum
import datetime
from wms.models import inventory_struct_lens_controller
from django.db import connections


class WcOrderStatusController:
    def new(self, request, parameters):
        rm = response_message()
        try:
            order_number = parameters['order_number']
            reference_code = parameters['reference_code']
            reference_code_2 = parameters.get('reference_code_2','')
            status_code = parameters['status_code']
            status_value = parameters['status_value']
            status_updated_at = parameters.get('status_updated_at','')

            wc_order_status.objects.get_or_create(
                **parameters
            )

            # update lbo
            try:
                LabOrder.objects.filter(lab_number=order_number).update(
                    vendor_order_reference=reference_code,
                    vendor_order_status_code=status_code,
                    vendor_order_status_value=status_value,
                    vendor_order_status_updated_at=status_updated_at
                )
            except Exception as ex:
                pass

        except Exception as ex:
            rm.capture_execption(ex)

        return rm
    
    def get_order_history(self, request, parameters):
        rm = response_message()
        vendor = parameters.get('vendor',0)
        order_number = parameters.get('order_number','')
        if vendor=='4':
            rm.obj = wc_order_status.objects.filter(order_number=order_number).order_by('-id')
        return rm

class PrescriptionType(Enum):
    NoneRx = 0  # 平光
    NearSightedness = 1  # 近视
    Presbyopia = 2  # 老花
    NearSightednessHighAstigmia = 3  # 近视高散
    PresbyopiaHighAstigmia = 4  # 老花高散
    Progressive = 5  # 渐进
    Prism = 6  # 棱镜

    Undefined = 99  # 未确定类型
    # 肯定需要转VD1000的FRAME
    # VD1000_FRAME_LIST = ('1812', '3654', '5419', '5420', '5745', '5746', '5816', '6710', '6711')
    # 只有平光需要转VD1000的FRAME
    # VD1000_FRAME_LIST_PLAIN = ('6709')


class PrescriptionController:
    def get_prescription_type(self, lbo):
        logging.debug('lbo od_sph[%s] od_sph_float[%s]' % (lbo.od_sph, float(lbo.od_sph)))
        # 平光
        if float(lbo.od_sph) == 0 and float(lbo.os_sph) == 0 \
                and float(lbo.od_cyl) == 0 and float(lbo.os_cyl) == 0 \
                and float(lbo.od_add) == 0 and float(lbo.os_add) == 0 \
                and float(lbo.od_prism) == 0 and float(lbo.os_prism) == 0:
            logging.debug('# option NoneRx //----------------------------------------//')
            return PrescriptionType.NoneRx
        # 近视普通散光
        elif float(lbo.od_sph) < 0 and float(lbo.os_sph) < 0 \
                and abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0:
            logging.debug('# option NearSightedness //----------------------------------------//')
            return PrescriptionType.NearSightedness
        # 近视高散
        elif float(lbo.od_sph) < 0 and float(lbo.os_sph) < 0 \
                and (abs(float(lbo.od_cyl)) > 2.0 or abs(float(lbo.os_cyl)) > 2.0):
            logging.debug('# option NearSightednessHighAstigmia //----------------------------------------//')
            return PrescriptionType.NearSightednessHighAstigmia
        # 老花普通散光
        elif float(lbo.od_sph) > 0 or float(lbo.os_sph) > 0 \
                and abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0:
            logging.debug('# option Presbyopia //----------------------------------------//')
            return PrescriptionType.Presbyopia
        # 老花高散
        elif float(lbo.od_sph) > 0 or float(lbo.os_sph) > 0 \
                and (abs(float(lbo.od_cyl)) > 2.0 or abs(float(lbo.os_cyl)) > 2.0):
            logging.debug('# option PresbyopiaHighAstigmia //----------------------------------------//')
            return PrescriptionType.PresbyopiaHighAstigmia
        # 渐进
        elif float(lbo.od_add) > 0.00 or float(lbo.os_add) > 0.00:
            logging.debug('# option Progressive //----------------------------------------//')
            return PrescriptionType.Progressive
        # 棱镜度
        elif float(lbo.od_prism) < 0.00 or float(lbo.os_prism) < 0.00:
            logging.debug('# option Prism //----------------------------------------//')
            return PrescriptionType.Prism
        else:
            logging.debug('# option Undefined //----------------------------------------//')
            return PrescriptionType.Undefined


class lens_contoller:
    def get_all(self, parameters):
        rm = response_message()
        dh = dict_helper()
        try:
            logging.debug('########################################')
            try:
                lenss = lens.objects.filter(is_enabled=True).order_by('-id')
                logging.debug('record count: %s' % lenss.count())
                rm.obj = lenss
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm

    def get_by_base_sku(self, parameters):
        rm = response_message()
        try:
            logging.debug('########################################')
            try:
                resp = parameters
                if not resp.code == 0:
                    return resp

                base_sku = resp.obj.get('lens_sku', '')
                vendor = resp.obj.get('vendor', '')
                filter = {}

                if not base_sku == '':
                    filter['base_sku'] = base_sku
                if not vendor == '':
                    filter['vendor_code'] = vendor

                logging.debug('base sku: %s' % base_sku)
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                logging.debug('record count: %s' % lenss.count())
                # logging.debug('lens sku: %s' % lenss[0].sku)
                rm.obj = lenss
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm

    def get_by_lbo(self, parameters):
        rm = response_message()
        try:
            logging.debug('########################################')
            try:
                resp = parameters
                if not resp.code == 0:
                    return resp

                lbo = resp.obj.get('lbo', None)

                base_sku = lbo.lens_sku
                vendor = resp.obj.get('vendor', '')

                base_sku_list = lens_extend.objects.filter(base_sku=base_sku).order_by('index')
                logging.debug(base_sku_list.query)

                if base_sku_list.count() > 0:
                    base_skus = []
                    for bs in base_sku_list:
                        base_skus.append(bs.sku)
                else:
                    base_skus = []
                    base_skus.append(base_sku)

                filter = {}

                if not base_sku == '':
                    filter['base_sku__in'] = base_skus
                if not vendor == '':
                    filter['vendor_code'] = vendor

                logging.debug('base sku: %s' % base_sku)
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                logging.debug('record count: %s' % lenss.query)
                # logging.debug('lens sku: %s' % lenss[0].sku)
                rm.obj = lenss
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm

    def get_by_vd(self, parameters):
        rm = response_message()
        try:
            logging.debug('########################################')
            try:
                resp = parameters
                if not resp.code == 0:
                    return resp

                vendor = resp.obj.get('vendor', '')
                index = resp.obj.get('index', '')
                filter = {}
                if not vendor == '':
                    filter['vendor_code'] = vendor

                if not index == '':
                    filter['index'] = index
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')

                logging.debug(lenss.query)

                rm.obj = lenss
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm

    def get_vd_lens_by_sku(self, parameters):
        rm = response_message()
        try:
            logging.debug('method: get_vd_lens_by_sku')
            logging.debug('parameters: %s' % parameters)
            try:
                sku = parameters.obj.get('sku', '')
                filter = {}
                if not sku == '':
                    filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter)

                if lenss.count() > 0:
                    olens = lenss[0]
                    rm.obj = olens
                else:
                    rm.code = -2
                    rm.message = 'SKU[ %s ] not found'
                    return rm

                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm


class lens_order_contoller:
    def get_all(self, parameters):
        rm = response_message()
        # dh = dict_helper()
        try:
            logging.debug('########################################')
            try:
                lenss = lens_order.objects.filter(is_enabled=True).order_by('-id')
                logging.debug('record count: %s' % lenss.count())
                rm.count = lenss.count()
                rm.obj = lenss
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))

            return rm

    def create(self, parameters):
        rm = response_message()
        try:
            logging.debug('########################################')
            try:
                usr = parameters.get('user', None)
                lbo = parameters.get('lbo', None)

                if lbo.is_lens_order_created:
                    rm.obj = None
                    rm.code = -4
                    rm.message = '该订单已创建 Lens Order, 系统不支持重复创建'
                    return rm

                lor = self.__create_lo(lbo)
                lor.rl_identification = 'R'

                lor.sph = lbo.od_sph
                lor.cyl = lbo.od_cyl
                lor.axis = lbo.od_axis

                lor.add = lbo.od_add
                lor.prism = lbo.od_prism
                lor.base = lbo.od_base
                lor.prism1 = lbo.od_prism1
                lor.base1 = lbo.od_base1

                if lbo.is_singgle_pd:
                    lor.pd = self.__get_pd(lbo)
                else:
                    lor.pd = lbo.od_pd

                lor.save()
                lof = self.__create_lo(lbo)
                lof.rl_identification = 'L'

                lof.sph = lbo.os_sph
                lof.cyl = lbo.os_cyl
                lof.axis = lbo.os_axis

                lof.add = lbo.os_add
                lof.prism = lbo.os_prism
                lof.base = lbo.os_base
                lof.prism1 = lbo.os_prism1
                lof.base1 = lbo.os_base1

                if lbo.is_singgle_pd:
                    lof.pd = self.__get_pd(lbo)
                else:
                    lof.pd = lbo.os_pd

                lof.save()

                lbo.is_lens_order_created = True
                lbo.save()

                from api.controllers.tracking_controllers import tracking_lab_order_controller
                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, usr, 'LENS_ORDER_CREATED')

                lens_order_obj = {}
                lens_order_obj['right'] = lor
                lens_order_obj['left'] = lof

                rm.obj = lens_order_obj
                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))

            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
            return rm

    def update_vendor(self, parameters):
        rm = response_message()
        try:
            logging.debug('# ----------------------------------------')
            logging.debug('method: update_vendor')
            logging.debug('input parameters: %s' % parameters)

            try:
                usr = parameters.get('user', None)
                lbo = parameters.get('lbo', None)
                vendor = parameters.get('vendor', '')
                lens_sku = parameters.get('lens_sku', '')
                lens_name = parameters.get('lens_name', '')

                lens_orders = lens_order.objects.filter(lab_number=lbo.lab_number)
                if lens_orders.count() == 0:
                    self.create(parameters)
                elif not lens_sku == '':
                    for lo in lens_orders:
                        lo.vendor = vendor
                        lo.lens_sku = lens_sku
                        lo.lens_name = lens_name
                        lo.save()

                    from api.controllers.tracking_controllers import tracking_lab_order_controller
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, usr, 'LENS_ORDER_CHANGED')

                return rm
            except Exception as e:
                rm.capture_execption(e)
                logging.debug(str(e))

            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
            return rm

    def __get_pd(self, lbo):
        pd = 0
        if lbo.is_singgle_pd:
            pd = lbo.pd / 2
        return pd

    def __create_lo(self, lbo):
        # lbo = LabOrder()
        lo = lens_order()
        lo.base_type = lbo.type
        lo.base_entity = lbo.id
        lo.order_number = lbo.order_number
        lo.lab_number = lbo.lab_number
        lo.user_id = 1
        lo.user_name = "SYSTEM"
        lo.vendor = lbo.vendor
        lo.lens_sku = lbo.act_lens_sku
        lo.lens_name = lbo.act_lens_name
        lo.vd_lens_sku = lbo.act_lens_sku
        lo.vd_lens_name = lbo.act_lens_name
        lo.quantity = 1

        lo.comments = lbo.comments

        return lo


class distribute_controller:
    def log(self, lbo, comments, status='SUCCESS', user=None):
        rm = response_message()
        try:
            dl = distribute_log()

            if user is None:
                dl.user_id = 1
                dl.user_name = 'System'
            else:
                try:
                    dl.user_id = user.id
                    dl.user_name = user.username
                except:
                    pass

            dl.comments = comments
            dl.status = status
            dl.base_type = lbo.type
            dl.base_entity = lbo.id
            dl.order_number = lbo.order_number
            dl.lab_number = lbo.lab_number
            dl.lens_sku = lbo.lens_sku
            dl.lens_name = lbo.lens_name
            dl.vd_lens_sku = lbo.act_lens_sku
            dl.vd_lens_name = lbo.act_lens_name
            dl.quantity = lbo.quantity
            dl.vendor = lbo.vendor
            dl.save()
        except Exception as e:
            logging.exception(str(e))
            rm.capture_execption(e)

        return rm

    def get_base_sku(self, lbo):
        rm = response_message()
        try:
            objs = {}
            base_sku = ''
            base_skus = []
            le = None
            les = lens_extend.objects.filter(is_enabled=True, base_sku=lbo.lens_sku).order_by('-id')

            count = les.count()

            if count == 0:
                objs['lens_sku'] = lbo.lens_sku
            elif count == 1:
                le = les[0]
                objs['lens_sku'] = le.sku
            else:
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if rx_type == PrescriptionType.NoneRx:
                    logging.debug('# option 1 //----------------------------------------//')
                    base_sku = 'KD56'
                    objs = self.__choose_stock_lens_vendor(lbo)

                elif rx_type == PrescriptionType.NearSightedness:
                    logging.debug('# option 2 //----------------------------------------//')
                    base_skus = []
                    base_skus.append('KD56-J')
                    base_skus.append('KD56-UVJ')
                    base_skus.append('KD59-J')
                    base_skus.append('KD61-J')
                    base_skus.append('KD61-UVJ')
                    base_skus.append('KD61-UVJ-8')
                    base_skus.append('KD67-J')
                    base_skus.append('KD67-UVJ')
                    base_skus.append('KD74-J')

                    if lbo.tint_sku == 'RS-H' \
                            or lbo.tint_sku == 'RS-C' \
                            or lbo.tint_sku == 'RS-L' \
                            or lbo.tint_sku == 'RJ-H' \
                            or lbo.tint_sku == 'RJ-C' \
                            or lbo.tint_sku == 'RJ-L':
                        base_skus = []
                        base_skus.append('KD56-JRS')
                        base_skus.append('KD56-JRJ')

                    for le in les:
                        if le.sku in base_skus:
                            objs['lens_sku'] = le.sku
                            break
                            #res = self.__choose_stock_lens_vendor(lbo)
                            #if not res['vendor'] == '':
                            #    objs = res
                            #break
                elif rx_type == PrescriptionType.Presbyopia:
                    logging.debug('# option 3 //----------------------------------------//')
                    base_skus = []
                    base_skus.append('KD56-L')
                    base_skus.append('KD56-UVL')
                    base_skus.append('KD59-L')
                    base_skus.append('KD61-L')
                    base_skus.append('KD61-UVL')
                    base_skus.append('KD61-UVL-8')
                    base_skus.append('KD67-L')
                    base_skus.append('KD67-UVL')
                    base_skus.append('KD74-L')

                    if lbo.tint_sku == 'RS-H' \
                            or lbo.tint_sku == 'RS-C' \
                            or lbo.tint_sku == 'RS-L' \
                            or lbo.tint_sku == 'RJ-H' \
                            or lbo.tint_sku == 'RJ-C' \
                            or lbo.tint_sku == 'RJ-L':
                        base_skus = []
                        base_skus.append('KD56-LRS')
                        base_skus.append('KD56-LRJ')
                    for le in les:
                        if le.sku in base_skus:
                            objs['lens_sku'] = le.sku
                            break

                elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                    logging.debug('# option 4 //----------------------------------------//')
                    base_skus = []
                    base_skus.append('KD56-JG')
                    base_skus.append('KD56-UVJG')
                    base_skus.append('KD59-JG')
                    base_skus.append('KD61-JG')
                    base_skus.append('KD61-UVJG')
                    base_skus.append('KD61-UVJG-8')
                    base_skus.append('KD67-JG')
                    base_skus.append('KD67-UVJG')
                    base_skus.append('KD74-JG')

                    if lbo.tint_sku == 'RS-H' \
                            or lbo.tint_sku == 'RS-C' \
                            or lbo.tint_sku == 'RS-L' \
                            or lbo.tint_sku == 'RJ-H' \
                            or lbo.tint_sku == 'RJ-C' \
                            or lbo.tint_sku == 'RJ-L':
                        rm.code = -3
                        rm.message = '没有找到对应的高散染色片'
                        return rm

                    for le in les:
                        if le.sku in base_skus:
                            objs['lens_sku'] = le.sku
                            break
                elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                    logging.debug('# option 5 //----------------------------------------//')
                    base_skus = []
                    base_skus.append('KD56-LG')
                    base_skus.append('KD56-UVLG')
                    base_skus.append('KD59-LG')
                    base_skus.append('KD61-LG')
                    base_skus.append('KD61-UVLG')
                    base_skus.append('KD61-UVLG-8')
                    base_skus.append('KD67-LG')
                    base_skus.append('KD67-UVLG')
                    base_skus.append('KD74-LG')

                    if lbo.tint_sku == 'RS-H' \
                            or lbo.tint_sku == 'RS-C' \
                            or lbo.tint_sku == 'RS-L' \
                            or lbo.tint_sku == 'RJ-H' \
                            or lbo.tint_sku == 'RJ-C' \
                            or lbo.tint_sku == 'RJ-L':
                        rm.code = -3
                        rm.message = '没有找到对应的高散染色片'
                        return rm

                    for le in les:
                        if le.sku in base_skus:
                            objs['lens_sku'] = le.sku
                            break

            if objs['lens_sku'] is None:
                rm.code = -2
                rm.message = 'Lens Not Found.'
            else:
                rm.obj = objs
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
        return rm

    def __choose_stock_lens_vendor(self, lbo):
        res = {}

        if abs(float(lbo.od_sph)) <= 3.0 and abs(float(lbo.os_sph)) <= 3.0 \
                and (not lbo.tint_sku) and (not '抗蓝' in lbo.lens_name) \
                and (not '膜变' in lbo.lens_name):
            res['vendor'] = 6
            res['lens_sku'] = 'KD56'
            return res
        else:
            return res

    def distribute_vendor(self, lbo, parameters):
        '''
        :param lbo:
        :param parameters: user or rm[response_message]
        :return:
        '''

        rm = response_message()
        AI_CODE = 'AI_DIST_90321'
        AI_CODE = 'AI_DIST_90514'
        AI_CODE = 'AI_DIST_200316'

        try:
            # 2020.04.13 by guof. OMS-729
            # --------------------start--------------------
            # 该段代码在以下两款SKU售罄之后可以删除
            # 如果Frame SKU 等于 1319C09或1320C09 则自动hold 标记为 STOCK_ORDER
            presc = PrescriptionController()
            rx_type = presc.get_prescription_type(lbo)
            pgi_lists = PgOrderItem.objects.filter(lab_order_number=lbo.lab_number)
            if len(pgi_lists) > 0:
                pgi_list = pgi_lists[0]
                if pgi_list.so_type == 'frame_only':
                    comments = '|自动分配到VD1000'
                    comments += '|自动分配-程序代码[%s]' % AI_CODE
                    lbo.vendor = 1000
                    lbo.comments_inner += comments

                    up_fields = {}
                    up_fields['vendor'] = 1000
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'Success')
                    rm.code = 0
                    rm.message = 'Lab Order distributed VD1000'
                    return rm


            pgorder_item = PgOrderItem.objects.filter(order_number=lbo.order_number)

            if (('1319C09' in lbo.frame or '1320C09' in lbo.frame or '4209G07' in lbo.frame)
                    and rx_type == PrescriptionType.NoneRx
                    and (lbo.act_ship_direction == 'STANDARD'
                         or (lbo.act_ship_direction == 'EXPRESS' and len(pgorder_item)==1))
                    and lbo.lens_sku in ('KD56L', 'KD59L')):
                lbo.vendor = '1001'
                lbo.comments_ship += ',STOCK_ORDER-由分拨中心发货'
                lbo.comments += ',STOCK_ORDER-由分拨中心发货'
                lbo.is_ai_checked = True
                lbo.save()
                return rm
            # --------------------end--------------------

            lens = LabProduct.objects.get(sku=lbo.lens_sku)

            logging.debug("lab_number: %s" % lbo.lab_number)

            # 分单标识
            distribute_mode = parameters.get('modify', '')

            # 排除的订单
            if ('蓝' in lbo.lens_name) and (not lens.is_rx_lab) \
                    and (not lbo.lens_sku == 'KD59L'):
                comments = '|抗蓝&PC镜片暂不做分配'
                comments += '|自动分配-程序代码[%s]' % AI_CODE
                lbo.comments_inner += comments

                up_fields = {}
                up_fields['comments_inner'] = comments
                self.__lbo_update(lbo.id, up_fields)

                self.log(lbo, comments, 'FAILED')
                rm.code = -5
                rm.message = '抗蓝&PC镜片暂不做分配'
                return rm

            # 2020.03.16 by guof. OMS-667
            # 排除所有 含 车房单光 的订单，人工分配
            # if ('车房单光' in lbo.lens_name):
            #     comments = '|车房单光镜片暂不分配'
            #     comments += '|AI-[%s]' % AI_CODE
            #     entity_id = lbo.id
            #     LabOrder.objects.get(id=entity_id).update(comments_inner=comments)
            #     rm.code = -6
            #     rm.message = '车房单光暂不分配'
            #     return rm

            # 如果订单的vendor不等于0，则不再进行二次分配
            if not int(lbo.vendor) == 0 and distribute_mode == '':
                comments = '|疑似重做订单,当前Vendor[%s]AI不作二次分配' % lbo.vendor
                comments += '|自动分配-程序代码[%s]' % AI_CODE
                lbo.comments_inner += comments

                up_fields = {}
                up_fields['comments_inner'] = comments
                self.__lbo_update(lbo.id, up_fields)

                self.log(lbo, comments, 'FAILED')
                rm.code = -2
                rm.message = 'Lab Order has beed distributed. '
                return rm

            # 如果镜架SKU在列表中直接分配到VD1000
            VD1000_FRAME_LIST = ('1812', '3654', '5419', '5420', '5745', '5746', '5816', '5819', '5821', '6710', '6711', '6709', '5822', '5820', '7302', '5320', '5819', '7313', '1335','1340')
            if lbo.frame[0:-3] in VD1000_FRAME_LIST:
                if float(lbo.os_sph) == 0 and float(lbo.os_sph) == 0 \
                        and float(lbo.os_cyl) == 0 and float(lbo.od_cyl) == 0:
                    comments = '|自动分配到VD1000'
                    comments += '|自动分配-程序代码[%s]' % AI_CODE
                    lbo.vendor = 1000
                    lbo.comments_inner += comments

                    up_fields = {}
                    up_fields['vendor'] = 1000
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'Success')
                    rm.code = 0
                    rm.message = 'Lab Order distributed VD1000'
                    return rm
                else:  # 不是平光添加备注并暂停
                    logging.debug(
                        str(lbo.os_sph) + ',' + str(lbo.od_sph) + ',' + str(lbo.os_cyl) + ',' + str(lbo.od_cyl) + ',')
                    comments = '|太阳镜无法应用RX,自动暂停'
                    comments += '|自动分配-程序代码[%s]' % AI_CODE
                    lbo.status = 'ONHOLD'
                    lbo.comments_inner += comments

                    up_fields = {}
                    up_fields['status'] = 'ONHOLD'
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'Success')
                    rm.code = -2
                    rm.message = 'Lab Order distributed VD1000 Error'
                    return rm

            # 如果镜架SKU在列表中(并且是平光)直接分配到VD1000
            VD1000_FRAME_LIST_PLAIN = '6709'
            if lbo.frame[0:-4] == VD1000_FRAME_LIST_PLAIN:
                if float(lbo.od_sph) == 0 and float(lbo.os_sph) == 0 \
                        and float(lbo.os_cyl) == 0 and float(lbo.od_cyl) == 0:
                    comments = '|自动分配到VD1000'
                    comments += '|自动分配-程序代码[%s]' % AI_CODE
                    lbo.vendor = 1000
                    lbo.comments_inner += comments

                    up_fields = {}
                    up_fields['vendor'] = 1000
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'Success')
                    rm.code = 0
                    rm.message = 'Lab Order distributed VD1000'
                    return rm
                else:  # 不是平光,不是偏光镜，不分VD1000,添加染色SKU，正常分配
                    if '偏光' not in lens.name:
                        logging.debug('添加染色')
                        comments = '|6709添加染色'
                        comments += '|自动分配-程序代码[%s]' % AI_CODE
                        lbo.tint_sku = 'RJ-H'
                        lbo.tint_name = '渐变染色-灰色'
                        lbo.comments_inner += comments

                        up_fields = {}
                        up_fields['tint_sku'] = 'RJ-H'
                        up_fields['tint_name'] = '渐变染色-灰色'
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)

            if lens.is_rx_lab:
                # 按计划镜片
                # 所有车房单光 自动分配给VD2
                if '车房单光' in lens.name:
                    rm = self.__factory_lens(lbo, parameters)
                else:
                    # 2020.01.07 by guof. OMS-573
                    # 所有的车房片 且框型为无框的 转给人工
                    if lbo.frame_type == 'Rimless':
                        comments = "| 车房订单 & 无框 暂时由人工分配"
                        lbo.comments_inner += comments

                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)

                        self.log(lbo, comments, "ignore")
                        rm.code = -1
                        rm.message = comments
                        return rm
                    else:
                        rm = self.__rx_lab(lbo, parameters)
            else:
                if rx_type == PrescriptionType.Progressive:
                    comments = '|库存片包含ADD，需人工受理-[%s]' % AI_CODE
                    lbo.comments_inner += comments
                    lbo.is_ai_checked = True

                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    up_fields['is_ai_checked'] = True
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'FAILED')
                    rm.code = -31
                    rm.message = 'Lab Order Prescription Type Is Progressive .'
                    return rm

                if rx_type == PrescriptionType.Prism:
                    comments = '|库存片包含PRISM，需人工受理-[%s]' % AI_CODE
                    lbo.comments_inner += comments
                    lbo.is_ai_checked = True

                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    up_fields['is_ai_checked'] = True
                    self.__lbo_update(lbo.id, up_fields)

                    self.log(lbo, comments, 'FAILED')
                    rm.code = -32
                    rm.message = 'Lab Order Prescription Type Is Prism .'
                    return rm

                rm = self.__stock_lens(lbo, parameters)

        except Exception as e:
            rm.capture_execption(e)
            self.log(lbo, str(e), 'EXCEPTION')

        return rm

    def __lbo_update(self, pk, fields={}):
        LabOrder.objects.filter(id=pk).update(**fields)

    # 车房片
    def __rx_lab(self, lbo, parameters):
        rm = response_message()
        try:
            lensc = lens_contoller()

            base_sku = self.get_base_sku(lbo)
            resp = lensc.get_by_base_sku(base_sku)
            parameters['rm'] = resp

            if not resp.code == 0:
                rm = resp
                self.log(lbo, rm.message, 'EXCEPTION')
                return rm
            else:
                self.__distribute(lbo, parameters)

        except Exception as e:
            rm.capture_execption(e)

        return rm

    # 库存片
    def __stock_lens(self, lbo, parameters):
        rm = response_message()
        try:
            # ----------------------------------------
            # 针对库存KD56单独进行分单
            # ----------------------------------------
            resp = response_message()

            filter = {}
            lenss = None
            sku = ''
            if lbo.lens_sku == 'KD56' and not lbo.tint_sku:
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if lbo.category_id == '3' or lbo.category_id == '6':
                    if rx_type == PrescriptionType.NoneRx:
                        sku = '8-KD59'
                    elif rx_type == PrescriptionType.NearSightedness:
                        sku = '8-KD59'
                    elif rx_type == PrescriptionType.Presbyopia:
                        sku = '8-KD59'
                    elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                        sku = '8-KD59'
                    elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                        sku = '8-KD59'
                    else:
                        sku = ''
                        rm.code = -55
                        rm.message = "All lens don't match!"
                        self.log(lbo, rm.message, 'EXCEPTION')
                        return rm
                else:
                    '''
                    2019.10.27 by guof.
                    增加基于 base_sku/sph/cyl 查询当前镜片库存量
                    '''
                    islc = inventory_struct_lens_controller()
                    parms = {}
                    od_lens_qty = 0
                    os_lens_qty = 0
                    bs_mr8 = "8-KD61"
                    parms["base_sku"] = bs_mr8
                    parms["sph"] = lbo.od_sph
                    parms["cyl"] = lbo.od_cyl
                    od_lens_qty = islc.get_qty(parms)
                    parms["base_sku"] = bs_mr8
                    parms["sph"] = lbo.os_sph
                    parms["cyl"] = lbo.os_cyl
                    os_lens_qty = islc.get_qty(parms)

                    if rx_type == PrescriptionType.NoneRx:
                        # 2019.11.4 by wj
                        # 暂时把6-KD56-C39 改为 8-KD61

                        # 2020.02.20 by guof.
                        # 恢复
                        # '判断膜层是否是单加硬'
                        if lbo.coating_sku == "HC":
                            sku = '6-KD56-HC'
                        else:
                            sku = '6-KD56-C39'
                    elif rx_type == PrescriptionType.NearSightedness:
                        if abs(float(lbo.od_sph)) <= 3.5 and abs(float(lbo.os_sph)) <= 3.5:
                            if lbo.frame_type.upper() == 'RIMLESS':
                                sku = '8-KD59'
                            elif od_lens_qty.count>0 and os_lens_qty.count>0:
                                sku = '8-KD61'
                            else:
                                # '判断膜层是否是单加硬'
                                if lbo.coating_sku == "HC":
                                    sku = '6-KD56-HC'
                                else:
                                    sku = '6-KD56-C39'
                        elif abs(float(lbo.od_sph)) > 3.5 or abs(float(lbo.os_sph)) > 3.5:
                            if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                                sku = '8-KD61'
                            else:
                                sku = '8-KD59'
                        else:
                            sku = '3-KD56-J'  # 近视超韧
                    elif rx_type == PrescriptionType.Presbyopia:
                        if abs(float(lbo.od_sph)) <= 3 and abs(float(lbo.os_sph)) <= 3:
                            if lbo.frame_type.upper() == 'RIMLESS':
                                sku = '8-KD59'
                            elif od_lens_qty.count>0 and os_lens_qty.count>0:
                                sku = '8-KD61'
                            else:
                                # '判断膜层是否是单加硬'
                                if lbo.coating_sku == "HC":
                                    sku = '6-KD56-HC'
                                else:
                                    sku = '6-KD56-C39'
                        elif abs(float(lbo.od_sph)) > 3 or abs(float(lbo.os_sph)) > 3:
                            if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                                sku = '8-KD61'
                            else:
                                sku = '8-KD59'
                        else:
                            sku = '3-KD56-L'
                    elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                        # 1.499CR39 200散光-300散光转库存片byzhutong 2020年11月12日
                        if abs(float(lbo.od_cyl)) <= 3 and abs(float(lbo.os_cyl)) <= 3:
                            sku = '6-KD56-C39'
                        else:
                            sku = '3-KD56-JG'
                    elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                        if abs(float(lbo.od_cyl)) <= 3 and abs(float(lbo.os_cyl)) <= 3:
                            sku = '6-KD56-C39'
                        else:
                            sku = '3-KD56-JG'
                    else:
                        sku = ''
                        rm.code = -55
                        rm.message = "All lens don't match!"
                        self.log(lbo, rm.message, 'EXCEPTION')
                        return rm
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss

            elif lbo.lens_sku == 'KDB56-C':
                # 2019.11.04 by wj
                # VD2的1.56膜变茶 分到 VD10 1.56基变茶
                # 2020.05.26 by wj
                # VD10的库存单光1.56基变茶的订单，分单到VD10；变更为车房单光1.56基变茶，分单到VD9
                #sku = "10-KDB56-C"
                sku = "5-CDB56-C"
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            # ----------------------------------------
            # 如果是KD61，不带染色 直接分到VD8
            # ----------------------------------------
            elif lbo.lens_sku == 'KD61' and not lbo.tint_sku:
                if (float(lbo.od_sph) < -6 or float(lbo.os_sph) < -6) and (
                        float(lbo.dia_1) > 75 or float(lbo.dia_1) < 50) and (abs(float(lbo.od_cyl)) > 3.0 or abs(float(lbo.os_cyl)) > 3.0):
                    comments = lbo.comments_inner + '|1.61MR-8库存单光超出度数或直径或散光范围'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    rm.code = -6
                    rm.message = '1.61MR-8库存单光超出度数或直径范围'
                    return rm
                #调整散光到-3
                elif ((float(lbo.od_sph) < -10 or (float(lbo.od_sph) > -6.25) and float(lbo.od_sph)<0)
                      or (float(lbo.os_sph) < -10 or (float(lbo.od_sph) > -6.25 and float(lbo.od_sph)<0))) \
                        and (float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50) and (abs(float(lbo.od_cyl)) > 3.0 or abs(float(lbo.os_cyl)) > 3.0):
                    comments = lbo.comments_inner + '|1.61MR-8库存单光超出度数或直径范围'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    rm.code = -6
                    rm.message = '1.61MR-8库存单光超出度数或直径范围'
                    return rm
                elif (float(lbo.od_sph) > 6 or float(lbo.os_sph) > 6) and (
                        float(lbo.dia_1) > 65 or float(lbo.dia_1) < 60) and (abs(float(lbo.od_cyl)) > 2.0 or abs(float(lbo.os_cyl)) > 2.0):
                    comments = lbo.comments_inner + '|1.61MR-8库存单光超出度数或直径或散光范围'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    rm.code = -6
                    rm.message = '1.61MR-8库存单光超出度数或直径范围'
                    return rm
                islc = inventory_struct_lens_controller()
                parms = {}
                bs_mr8 = "8-KD61"
                parms["base_sku"] = bs_mr8
                parms["sph"] = lbo.od_sph
                parms["cyl"] = lbo.od_cyl
                od_lens_qty = islc.get_qty(parms)
                parms["base_sku"] = bs_mr8
                parms["sph"] = lbo.os_sph
                parms["cyl"] = lbo.os_cyl
                os_lens_qty = islc.get_qty(parms)
                if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                    sku = '8-KD61'
                else:
                    sku = '10-KD61'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            elif lbo.lens_sku == 'KD61' and lbo.tint_sku:
                # 20200722把库存单光1.61实色染色灰的近视，光度在600散光200范围内的订单分到6-KD61-H
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if lbo.tint_sku == 'RS-H':
                    if rx_type == PrescriptionType.NearSightedness:
                        if abs(float(lbo.od_sph)) <= 6.0 and abs(float(lbo.os_sph)) <= 6.0:
                            sku = '6-KD61-H'
                        else:
                            sku = '7-KD61-RS-8'
                        filter['sku'] = sku
                        lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                        resp.obj = lenss
                    else:
                        lensc = lens_contoller()
                        base_sku = self.get_base_sku(lbo)
                        resp = lensc.get_by_base_sku(base_sku)
                else:
                    lensc = lens_contoller()
                    base_sku = self.get_base_sku(lbo)
                    resp = lensc.get_by_base_sku(base_sku)
            # ----------------------------------------
            # 如果是KDB59-C，KDB59-H,KDB59L-C,KDB59L-H 不带染色 直接分到VD3
            # ----------------------------------------
            elif lbo.lens_sku == 'KDB59-C' and not lbo.tint_sku: # 库存单光膜变PC1.59 茶色 + HMC
                sku = '3-KD59-BC'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            elif lbo.lens_sku == 'KDB59-H' and not lbo.tint_sku: # 库存单光膜变PC1.59 灰色 + HMC
                sku = '3-KD59-BH'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            elif lbo.lens_sku == 'KDB59L-C' and not lbo.tint_sku: # 库存单光-PC1.59抗蓝光+膜变-茶色 + HMC
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if rx_type == PrescriptionType.NoneRx:
                    sku = '8-KD59L'
                elif rx_type == PrescriptionType.NearSightedness:
                    sku = '3-KD59-UVBC'
                elif rx_type == PrescriptionType.Presbyopia:
                    sku = '3-KD59-UVBCL'
                elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                    sku = '3-KD59-UVBC'
                elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                    sku = '3-KD59-UVBCL'
                else:
                    sku = ''
                    rm.code = -55
                    rm.message = "All lens don't match!"
                    self.log(lbo, rm.message, 'EXCEPTION')
                    return rm
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            elif lbo.lens_sku == 'KDB59L-H' and not lbo.tint_sku: # 库存单光-PC1.59抗蓝光+膜变-灰色 + HMC
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if rx_type == PrescriptionType.NoneRx:
                    sku = '8-KD59L'
                elif rx_type == PrescriptionType.NearSightedness:
                    sku = '3-KD59-UVBH'
                elif rx_type == PrescriptionType.Presbyopia:
                    sku = '3-KD59-UVBHL'
                elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                    sku = '3-KD59-UVBH'
                elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                    sku = '3-KD59-UVBHL'
                else:
                    sku = ''
                    rm.code = -55
                    rm.message = "All lens don't match!"
                    self.log(lbo, rm.message, 'EXCEPTION')
                    return rm
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss

            # ----------------------------------------
            # 如果是KD56，带染色 根据不同的染色需求确定不同的SKU
            # ----------------------------------------
            elif lbo.lens_sku == 'KD56' and lbo.tint_sku:
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                #修改自动分单，库存染色分到vd9,超出范围分到vd7
                #20200722把库存单光1.56实色染色灰近视，光度在600散光200范围内的订单分到6-KD61-H
                if lbo.tint_sku == 'RS-H':
                    if rx_type == PrescriptionType.NearSightedness:
                        if abs(float(lbo.od_sph)) <= 6.0 and abs(float(lbo.os_sph)) <= 6.0:
                            sku = '6-KD61-H'
                        else:
                             sku = '7-KD56-RS'
                    elif rx_type == PrescriptionType.Presbyopia:
                        if abs(float(lbo.od_sph)) <= 2.0 and abs(float(lbo.os_sph)) <= 2.0:
                            sku = '5-KD56'
                        else:
                            sku = '7-KD56-RS'
                elif lbo.tint_sku == 'RS-C' or lbo.tint_sku == 'RS-L':
                    if rx_type == PrescriptionType.NearSightedness:
                        if abs(float(lbo.od_sph)) <= 4.0 and abs(float(lbo.os_sph)) <= 4.0:
                            sku = '5-KD56'
                        else:
                            sku = '7-KD56-RS'
                    elif rx_type == PrescriptionType.Presbyopia:
                        if abs(float(lbo.od_sph)) <= 2.0 and abs(float(lbo.os_sph)) <= 2.0:
                            sku = '5-KD56'
                        else:
                            sku = '7-KD56-RS'
                elif lbo.tint_sku == 'RJ-C' or lbo.tint_sku == 'RJ-H' or lbo.tint_sku == 'RJ-L':
                    if rx_type == PrescriptionType.NearSightedness:
                            if abs(float(lbo.od_sph)) <= 4.0 and abs(float(lbo.os_sph)) <= 4.0:
                                sku = '5-KD56'
                            else:
                                sku = '7-KD56-RJ'
                    elif rx_type == PrescriptionType.Presbyopia:
                        if abs(float(lbo.od_sph)) <= 2.0 and abs(float(lbo.os_sph)) <= 2.0:
                            sku = '5-KD56'
                        else:
                            sku = '7-KD56-RJ'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            # ----------------------------------------
            # 如果是KD56L抗蓝，则只根据不同
            # ----------------------------------------
            elif lbo.lens_sku == 'KD56L' and not lbo.tint_sku:
                presc = PrescriptionController()
                rx_type = presc.get_prescription_type(lbo)
                if lbo.category_id == '3' or lbo.category_id == '6':
                    if rx_type == PrescriptionType.NoneRx \
                            or rx_type == PrescriptionType.NearSightedness:
                        sku = '8-KD59L'  # 近视超韧
                    elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                        sku = '8-KD59L'
                    elif rx_type == PrescriptionType.Presbyopia:
                        sku = '8-KD59L'
                    elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                        sku = '8-KD59L'
                    else:
                        pass
                else:
                    if rx_type == PrescriptionType.NoneRx \
                            or rx_type == PrescriptionType.NearSightedness:
                        sku = '3-KD56-J'  # 近视超韧
                    elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                        sku = '3-KD56-JG'
                    elif rx_type == PrescriptionType.Presbyopia:
                        #对于1.56库存单光抗蓝老花镜片直径超过68的做调整分单到5-CD56L
                        if float(lbo.dia_1) > 68:
                            sku = '5-CD56L'
                        else:
                            sku = '3-KD56-L'
                    elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                        #对于1.56库存单光抗蓝老花镜片直径超过68的做调整分单到5-CD56L
                        if float(lbo.dia_1) > 68:
                            sku = '5-CD56L'
                        else:
                            sku = '3-KD56-LG'
                    else:
                        pass
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            # ----------------------------------------
            # 如果是KD59L抗蓝PC，分VD8
            # ----------------------------------------
            elif lbo.lens_sku == 'KD59L' and not lbo.tint_sku:
                sku = '8-KD59L'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            # ----------------------------------------
            # 如果是KD59，直接分到VD8
            # ----------------------------------------
            elif lbo.lens_sku == 'KD59' and not lbo.tint_sku:
                if (float(lbo.od_sph) < -6 or float(lbo.os_sph) < -6) and (
                        float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50) and (abs(float(lbo.od_cyl)) > 2.0 or abs(float(lbo.os_cyl)) > 2.0):
                    comments = lbo.comments_inner + '|1.59PC库存单光超出度数或直径或散光范围'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    rm.code = -6
                    rm.message = '1.59PC库存单光超出度数或直径范围'
                    return rm
                #度数由+4调整到+4.5
                elif (float(lbo.od_sph) > 4.5 or float(lbo.os_sph) > 4.5) and (
                        float(lbo.dia_1) > 65 or float(lbo.dia_1) < 60) and (abs(float(lbo.od_cyl)) > 2.0 or abs(float(lbo.os_cyl)) > 2.0):
                    comments = lbo.comments_inner + '|1.59PC库存单光超出度数或直径或散光范围'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    rm.code = -6
                    rm.message = '1.59PC库存单光超出度数或直径范围'
                    return rm
                else:
                    islc = inventory_struct_lens_controller()
                    parms = {}
                    bs_sku = '8-KD59'
                    parms["base_sku"] = bs_sku
                    parms["sph"] = lbo.od_sph
                    parms["cyl"] = lbo.od_cyl
                    od_lens_qty = islc.get_qty(parms)
                    parms["base_sku"] = bs_sku
                    parms["sph"] = lbo.os_sph
                    parms["cyl"] = lbo.os_cyl
                    os_lens_qty = islc.get_qty(parms)
                    if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                        sku = '8-KD59'
                    else:
                        #1.59PC库存单光库存不足分单到1.59PC库存单光抗蓝光
                        sku = '8-KD59L'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            # ----------------------------------------
            # 不影响特定SKU之外的流程
            # ----------------------------------------
            elif lbo.lens_sku == 'KDB56-H':
                if lbo.category_id == '3' or lbo.category_id == '6':

                    # presc = PrescriptionController()
                    # rx_type = presc.get_prescription_type(lbo)
                    # if rx_type == PrescriptionType.NoneRx \
                    #         or rx_type == PrescriptionType.NearSightedness:
                    #     sku = '3-KD59-UVBH'  # 库存单光-PC1.59抗蓝光+膜变-灰色 + HMC近视
                    # elif rx_type == PrescriptionType.NearSightednessHighAstigmia:
                    #     sku = '3-KD59-UVBH'
                    # elif rx_type == PrescriptionType.Presbyopia:
                    #     sku = '3-KD59-UVBHL' # 库存单光-PC1.59抗蓝光+膜变-灰色 + HMC老花
                    # elif rx_type == PrescriptionType.PresbyopiaHighAstigmia:
                    #     sku = '3-KD59-UVBHL'
                    # else:
                    #     pass
                    #2020 05 26 by wj
                    #库存单光1.56膜变灰--儿童光学镜，分单到VD2--PC1.59膜变灰，变更为库存单光1.56抗蓝变色灰，分单到VD6
                    sku = '6-KDB56L-H'
                else:
                    sku = '6-KDB56L-H'
                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                resp.obj = lenss
            elif lbo.lens_sku == 'KD67' and not lbo.tint_sku:
                if ((float(lbo.od_sph) < 0 and float(lbo.od_sph) >= -12) and (float(lbo.os_sph) < 0 and float(lbo.os_sph) >= -12)) and (abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0):
                    sku = '10-KD67'
                    filter['sku'] = sku
                    lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                    resp.obj = lenss
                else:
                    lensc = lens_contoller()
                    base_sku = self.get_base_sku(lbo)
                    resp = lensc.get_by_base_sku(base_sku)
            elif lbo.lens_sku == 'KD67L' and not lbo.tint_sku:
                if ((float(lbo.od_sph) <= -3 and float(lbo.od_sph) >= -12) and (float(lbo.os_sph) <= -3 and float(lbo.os_sph) >= -12)) and (abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0):
                    sku = '10-KD67L'
                    filter['sku'] = sku
                    lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                    resp.obj = lenss
                else:
                    lensc = lens_contoller()
                    base_sku = self.get_base_sku(lbo)
                    resp = lensc.get_by_base_sku(base_sku)
            else:
                lensc = lens_contoller()
                base_sku = self.get_base_sku(lbo)
                resp = lensc.get_by_base_sku(base_sku)

            if not resp.code == 0:
                rm = resp
                self.log(lbo, rm.message, 'EXCEPTION')
                return rm
            else:
                parameters['rm'] = resp
                self.__distribute(lbo, parameters)
        except Exception as e:
            rm.capture_execption(e)

        return rm

    # @transaction.commit_on_success
    def __distribute(self, lbo, parameters):

        logging.debug('Method: __distribute')
        logging.debug('Input Parameters: %s' % parameters)

        rm = response_message()

        VD2_LIMIT = 100
        user_obj = parameters.get('user', None)
        mode = parameters.get('modify', '')
        vendor_code = parameters.get('vendor', '')
        lens_sku = parameters.get('lens_sku', '')
        lens_name = parameters.get('lens_name', '')
        loc = lens_order_contoller()

        if mode == '':
            logging.debug('mode: 自动分单')
            try:
                dc = distribute_configuration.objects.get(is_enabled=True, key='VD2_LIMIT')
                lmt = int(dc.value)
                VD2_LIMIT = lmt
            except:
                pass

            rm = parameters.get('rm', None)

            if not rm:
                logging.debug("没有找到对应的镜片")

            if not rm.code == 0:
                return rm

            lenss = rm.obj
            lenso = lenss[0]
            logging.debug("lens sku: %s" % lenso.sku)
            logging.debug("lens name: %s" % lens_name)

            vendor_code = lenso.vendor_code

            if vendor_code == '3':
                lbos = LabOrder.objects.filter(is_enabled=True).filter(vendor='2',
                                                                       create_at__gte=datetime.datetime.now().date())
                count = lbos.count()
                logging.debug('date:%s count:%s' % (datetime.datetime.now().date(), count))
                if count < VD2_LIMIT:
                    vendor_code = '2'

                # hold the vendor 3 from 2019.05
                vendor_code = '2'

            lens_sku = lenso.sku
            lens_name = lenso.name

            #平顶双光1.56自动分单到VD4后需要把品种改为平顶双光1.50  20200825
            if lenso.base_sku == 'CP56' and vendor_code == '4':
                lens_sku = '4-CP50'
                lens_name = '车房平顶双光1.50'

            lbo.act_lens_sku = lens_sku
            lbo.act_lens_name = lens_name
            # 星期一到星期五，所有VD5分给VD9，星期六，正常，星期日下午1点后所有VD5分给VD9
            # utc_time = datetime.datetime.now()
            # hour = datetime.timedelta(hours=8)
            # beijing_time = utc_time + hour
            # week = utc_time.weekday()
            # week in (0, 1, 2, 3, 4) and
            if vendor_code == '5':
                lbo.vendor = '9'
            # elif week == 6 and vendor_code == '5':
            #     one_time_hour = datetime.datetime.strptime('13:00', '%H:%M').time()
            #     utc_time_hour = utc_time.time()
            #     if utc_time_hour < one_time_hour:
            #         lbo.vendor = '9'
            #     else:
            #         lbo.vendor = vendor_code
            else:
                lbo.vendor = vendor_code

            lbo.save()

            paras = {}
            paras['lbo'] = lbo
            paras['user'] = user_obj

            rm = loc.create(paras)
            if not rm.code == 0:
                return rm

        elif mode == 'MANUAL':
            logging.debug('MANUAL 手动分单 ....')

            if (not lbo.status == ''
                    and not lbo.status is None
                    and not lbo.status == 'REQUEST_NOTES'
                    and not lbo.status == 'FRAME_OUTBOUND'
                    and not lbo.status == 'LENS_REGISTRATION'):
                rm.code = -3
                rm.message = '只有在新订单/出库申请/镜架出库/来片登记状态才允许修改镜片'

            if not lens_sku == '':
                loc.update_vendor(parameters)

            qualified = parameters.get('qualified', '')
            if not qualified == '':
                logging.debug('qualified sign: %s' % qualified)
                is_qualified = True
                from qc.models import preliminary_checking_control
                pcc = preliminary_checking_control()

                request = parameters.get('request', None)
                lab_number = parameters.get('lab_number', '')
                reason_code = parameters.get('reason_code', '')
                reason = parameters.get('reason', '')
                act_lens_sku = ''  # parameters.get('lens_sku', '')
                act_lens_name = ''  # parameters.get('lens_name', '')

                resp = pcc.add(
                    request,
                    lab_number,
                    is_qualified,
                    reason_code,
                    reason,
                    act_lens_sku,
                    act_lens_name,
                )
                if not resp.code == 0:
                    return resp

            if not lens_sku == '':
                logging.debug('lens_sku: %s' % lens_sku)
                lbo.vendor = vendor_code
                lbo.act_lens_sku = lens_sku
                lbo.act_lens_name = lens_name

                lbo.save()

        self.log(lbo, '', 'SUCCESS', user_obj)

        return rm

    def distribute_vendor_manual(self, parameters):
        '''
        :param lbo:
        :param parameters: user or rm[response_message]
        :return:
        '''

        logging.debug("distribute vendor manual ....")

        rm = response_message()
        try:
            lbo = parameters.get('lbo', None)
            rm = self.__distribute(lbo, parameters)

        except Exception as e:
            rm.capture_execption(e)
            self.log(lbo, str(e), 'EXCEPTION')

        return rm


    def __factory_lens(self, lbo, parameters):
        rm = response_message()
        try:
            presc = PrescriptionController()
            rx_type = presc.get_prescription_type(lbo)

            filter = {}
            lenss = None
            sku = ''
            if float(lbo.od_prism) > 0.00 or float(lbo.os_prism) > 0.00 or float(lbo.od_prism1) > 0.00 or float(lbo.os_prism1) > 0.00:
                rm = self.__rx_lab(lbo, parameters)
                comments = '|车房单光镜片带有棱镜需人工处理,走车房单分单规则'
                up_fields = {}
                up_fields['comments_inner'] = comments
                self.__lbo_update(lbo.id, up_fields)
                return rm

            #2020-11-19zhutong修改
            if float(lbo.od_sph) > 0 and float(lbo.os_sph) > 0:
                if lbo.lens_sku in ('CD56') and not lbo.tint_sku and ((abs(float(lbo.od_cyl)) > 2.0 and abs(float(lbo.od_cyl)) <= 3.0) or (abs(float(lbo.os_cyl)) > 2.0 and abs(float(lbo.os_cyl)) <= 3.0)):
                    sku = '6-KD56-C39'

            if float(lbo.od_sph) <= 0 and float(lbo.os_sph) <= 0:
                if lbo.lens_sku in ('CD56') and not lbo.tint_sku and ((abs(float(lbo.od_cyl)) > 2.0 and abs(float(lbo.od_cyl)) <= 3.0) or (abs(float(lbo.os_cyl)) > 2.0 and abs(float(lbo.os_cyl)) <= 3.0)):
                    if (abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6) and float(lbo.dia_1) > 77:
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    else:
                        # sku = '10-KD61'
                        sku = '6-KD56-C39'  #2020-11-19zhutong修改

                #2020-11-23zhutong 1570到1612行
                elif lbo.lens_sku in ('CD56','CD61') and not lbo.tint_sku and ((abs(float(lbo.od_cyl)) >= 0.0 and abs(float(lbo.od_cyl)) <= 2.0) or (abs(float(lbo.os_cyl)) >= 0.0 and abs(float(lbo.os_cyl)) <= 2.0)):
                    if ((0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6)) and (65 <= float(lbo.dia_1) <= 75):
                        sku = '10-KD61'
                    if ((6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10)) and (65 <= float(lbo.dia_1) <= 70):
                        sku = '10-KD61'
                elif lbo.lens_sku in ('CD67') and not lbo.tint_sku and ((abs(float(lbo.od_cyl)) >= 0.0 and abs(float(lbo.od_cyl)) <= 2.0) or (abs(float(lbo.os_cyl)) >= 0.0 and abs(float(lbo.os_cyl)) <= 2.0)):
                    if ((0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6)) and (65 <= float(lbo.dia_1) <= 75):
                        sku = '10-KD67'
                    if ((6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10)) and (65 <= float(lbo.dia_1) <= 70):
                        sku = '10-KD67'
                elif lbo.lens_sku in ('CD56L', 'CD61L') and (0 <= abs(float(lbo.od_cyl)) <= 2.0) and (0 < abs(float(lbo.os_cyl)) <= 2.0):
                    if (0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6) and ( 65 <= float(lbo.dia_1) <= 75):
                        sku = '10-KD61L'
                    if (6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10) and ( 65 <= float(lbo.dia_1) <= 70):
                        sku = '10-KD61L'
                elif lbo.lens_sku in ('CD67') and (0 <= abs( (lbo.od_cyl)) <= 2.0) and (0 < abs(float(lbo.os_cyl)) <= 2.0):
                    if (0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6) and ( 65 <= float(lbo.dia_1) <= 75):
                        sku = '3-KD67L'
                    if (6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10) and ( 65 <= float(lbo.dia_1) <= 70):
                        sku = '3-KD67L'
                elif lbo.lens_sku in ('CD56', 'CD61') and lbo.tint_sku and (0 <= abs(float(lbo.od_cyl)) <= 2.0) and (0 < abs(float(lbo.os_cyl)) <= 2.0):
                    if (0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6) and ( 65 <= float(lbo.dia_1) <= 75):
                        if 'RS' in lbo.tint_sku:
                            sku = '7-KD61-RS-7'
                        else:
                            sku = '7-KD61-RJ-7'
                    if (6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10) and ( 60 <= float(lbo.dia_1) <= 70):
                        if 'RS' in lbo.tint_sku:
                            sku = '7-KD61-RS-7'
                        else:
                            sku = '7-KD61-RJ-7'
                elif lbo.lens_sku in ('CD67') and lbo.tint_sku and (0 <= abs(float(lbo.od_cyl)) <= 2.0) and (0 < abs(float(lbo.os_cyl)) <= 2.0):
                    if (0 <= abs(float(lbo.od_sph)) <= 6) or (0 <= abs(float(lbo.os_sph)) <= 6) and ( 65 <= float(lbo.dia_1) <= 75):
                        if 'RS' in lbo.tint_sku:
                            sku = '7-KD67-RS-7'
                        else:
                            sku = '7-KD67-RJ-7'
                    if (6.25 <= abs(float(lbo.od_sph)) <= 10) or (6.25 <= abs(float(lbo.os_sph)) <= 10) and ( 60 <= float(lbo.dia_1) <= 70):
                        if 'RS' in lbo.tint_sku:
                            sku = '7-KD67-RS-7'
                        else:
                            sku = '7-KD67-RJ-7'
                elif lbo.lens_sku in ('CD56', 'CD67')and not lbo.tint_sku and abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0:
                    if (abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6) and (float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    elif abs(float(lbo.od_sph)) <= 6 and abs(float(lbo.os_sph)) <= 6 and (float(lbo.dia_1) > 75 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    else:
                        if lbo.lens_sku == 'CD67':
                            sku = '10-KD67'
                        else:
                            islc = inventory_struct_lens_controller()
                            parms = {}
                            bs_sku = '8-KD61'
                            parms["base_sku"] = bs_sku
                            parms["sph"] = lbo.od_sph
                            parms["cyl"] = lbo.od_cyl
                            od_lens_qty = islc.get_qty(parms)
                            parms["base_sku"] = bs_sku
                            parms["sph"] = lbo.os_sph
                            parms["cyl"] = lbo.os_cyl
                            os_lens_qty = islc.get_qty(parms)
                            if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                                sku = '8-KD61'
                            else:
                                sku = '10-KD61'
                elif lbo.lens_sku in ('CD61') and not lbo.tint_sku and abs(float(lbo.od_cyl)) <= 3.0 and abs(float(lbo.os_cyl)) <= 3.0:
                    if (abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6) and (
                            float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    elif abs(float(lbo.od_sph)) <= 6 and abs(float(lbo.os_sph)) <= 6 and (
                            float(lbo.dia_1) > 75 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    else:
                        if lbo.lens_sku == 'CD67':
                            sku = '10-KD67'
                        else:
                            islc = inventory_struct_lens_controller()
                            parms = {}
                            bs_sku = '8-KD61'
                            parms["base_sku"] = bs_sku
                            parms["sph"] = lbo.od_sph
                            parms["cyl"] = lbo.od_cyl
                            od_lens_qty = islc.get_qty(parms)
                            parms["base_sku"] = bs_sku
                            parms["sph"] = lbo.os_sph
                            parms["cyl"] = lbo.os_cyl
                            os_lens_qty = islc.get_qty(parms)
                            if od_lens_qty.count > 0 and os_lens_qty.count > 0:
                                sku = '8-KD61'
                            else:
                                sku = '10-KD61'
                elif lbo.lens_sku in ('CD56', 'CD61', 'CD67') and lbo.tint_sku and abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0:
                    if (abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6) and (float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    elif abs(float(lbo.od_sph)) <= 6 and abs(float(lbo.os_sph)) <= 6 and (float(lbo.dia_1) > 75 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    else:
                        if lbo.lens_sku == 'CD67':
                            if 'RS' in lbo.tint_sku:
                                sku = '7-KD67-RS-7'
                            else:
                                sku = '7-KD67-RJ-7'
                        elif lbo.lens_sku == 'CD56':
                            #符合规则度数大于6 分到7-KD61-RS-8，7-KD61-RJ-8；度数小于6直径大于70分到7-KD61-RS-8,7-KD61-RJ-8;直径小于70
                            #分单到7-KD56-RS，7-KD56-RJ
                            if abs(float(lbo.od_sph)) <= 6 and abs(float(lbo.os_sph)) <= 6:
                                if float(lbo.dia_1) > 70:
                                    if 'RS' in lbo.tint_sku:
                                        sku = '7-KD61-RS-8'
                                    else:
                                        sku = '7-KD61-RJ-8'
                                else:
                                    if 'RS' in lbo.tint_sku:
                                        sku = '7-KD56-RS'
                                    else:
                                        sku = '7-KD56-RJ'
                            else:
                                if 'RS' in lbo.tint_sku:
                                    sku = '7-KD61-RS-8'
                                else:
                                    sku = '7-KD61-RJ-8'
                        else:
                            if 'RS' in lbo.tint_sku:
                                sku = '7-KD61-RS-8'
                            else:
                                sku = '7-KD61-RJ-8'
                elif lbo.lens_sku in ('CD56L', 'CD61L', 'CD67L') and abs(float(lbo.od_cyl)) <= 2.0 and abs(float(lbo.os_cyl)) <= 2.0:
                    if (abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6) and (float(lbo.dia_1) > 70 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    elif abs(float(lbo.od_sph)) <= 6 and abs(float(lbo.os_sph)) <= 6 and (float(lbo.dia_1) > 75 or float(lbo.dia_1) < 50):
                        rm = self.__rx_lab(lbo, parameters)
                        comments = lbo.comments_inner + '|车房单光镜片超出库存度数或直径范围, 走车房单分单规则'
                        up_fields = {}
                        up_fields['comments_inner'] = comments
                        self.__lbo_update(lbo.id, up_fields)
                        return rm
                    else:
                        if lbo.lens_sku == 'CD67L':
                            sku = '3-KD67-UVJ-7'
                            #由'3-KD67-UVJ-7' 调整为'3-KD67-J-7'
                            #sku = '3-KD67-J-7'
                        else:
                            sku = '10-KD61L'
                else:
                    rm = self.__rx_lab(lbo, parameters)
                    comments = '|车房单光镜片未找到库存对应镜片, 走车房单分单规则'
                    up_fields = {}
                    up_fields['comments_inner'] = comments
                    self.__lbo_update(lbo.id, up_fields)
                    return rm

                filter['sku'] = sku
                lenss = lens.objects.filter(is_enabled=True).filter(**filter).order_by('priority')
                rm.obj = lenss
                parameters['rm'] = rm
                self.__distribute(lbo, parameters)
            else:
                rm = self.__rx_lab(lbo, parameters)
                comments = '|车房单光镜片未找到库存对应镜片, 走车房单分单规则'
                up_fields = {}
                up_fields['comments_inner'] = comments
                self.__lbo_update(lbo.id, up_fields)
                return rm

        except Exception as e:
            rm.capture_execption(e)

        return rm



class WxOrderStatusController:
    def get_order_history(self, request, parameters):
        rm = response_message()
        vendor = parameters.get('vendor', 0)
        order_number = parameters.get('order_number', '')
        if vendor == '9':
            rm.obj = WxOrderStatus.objects.filter(order_number=order_number).order_by('-id')
        return rm
