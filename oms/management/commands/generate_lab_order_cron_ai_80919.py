# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.db.models import Q

from django.http import HttpRequest
from oms.controllers.order_controller import *
from oms.models.post_models import Prescription
from oms.models.product_models import PgProduct

from tracking.models import ai_log_control


class Command(BaseCommand):
    AI_CODE = 'AI_80919_90528'
    # 记录LOG 的开关
    write_log = True

    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')

        '''
         81001:增加对订单中包含特别说明或包含测试用的COUPON_CODE的过滤
         81008:修复订单中包含特别说明，影响其他单光订单下单的BUG
        '''

        index = 0

        ailog = ai_log_control()  # AI操作日志

        try:
            # Pg Order List:

            pgos = PgOrder.objects.filter(is_enabled=True,
                                          is_inlab=False,
                                          status='processing').filter(~Q(status_control='APPROVED'),
                                                                      ~Q(status_control='REVIEWED'))

            logging.critical(pgos.query)

            msg = '(%s):%s: %s'

            '''
             AI_CODE:AI_80919
             
             检索所有状态正常，Not Inlab，Status=processing的订单
             检索：
             1.该订单下的所有Pg Order Item中的镜片为单光库存片
             2.所有验光单中散光度<=200
             3.ADD为0
             4.PRISM为0
             
             理论上讲，如果是单光，上述的验光单数据一定为0，但仍需验证
            '''
            '''
                2019.07.27 --by gaoyu
                每个渐进订单，重新调用接口查询，pupils_position
            '''
            approved_pgos = []

            for pgo in pgos:
                logging.critical(msg % (str(index), pgo.order_number, pgo.status))
                index += 1
                is_can_auto = True

                # 筛选生成不足一小时的订单
                now_time = datetime.datetime.now()
                pg_time = pgo.create_at
                dt = pg_time.replace(tzinfo=None)
                dt = dt + datetime.timedelta(hours=+8)
                # 记录LOG
                if self.write_log:
                    ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单-时间筛选1', str(now_time), str(pg_time),
                              str(dt),
                              str((now_time - dt).seconds), '', 'YES', ' 时间')
                if (now_time - dt).seconds < 3600:
                    logging.critical('订单创建不足一小时 不开始自动下单')
                    # 记录LOG
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单-时间筛选2', str(now_time), str(pg_time),
                                  str(dt), str((now_time - dt).seconds), '', 'YES', ' 时间')
                    is_can_auto = False
                    continue

                if pgo.is_inst:
                    logging.critical('包含特别说明 无法自动生成')
                    # 记录LOG
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'is_inst', str(pgo.is_inst), '', '',
                                  '', 'YES', '包含特别说明 无法自动生成')

                    is_can_auto = False
                    continue

                if pgo.coupon_code == 'PG-INTERNAL':
                    logging.critical('内部测试订单 无法自动生成')
                    # 记录LOG
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'coupon_code', pgo.coupon_code, '',
                                  '',
                                  '', 'YES', '内部测试订单 无法自动生成')

                    is_can_auto = False
                    continue

                if pgo.coupon_code:
                    if bool(re.search('REPLACE', pgo.coupon_code, re.IGNORECASE)):
                        logging.critical('替换订单 无法自动生成')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'coupon_code', pgo.coupon_code,
                                      '',
                                      '', '', 'YES', '替换订单 无法自动生成')

                        is_can_auto = False
                        continue
                # 包含instruction不过
                if not pgo.instruction == '' and not pgo.instruction == 'null' and pgo.instruction is not None:
                    is_can_auto = False
                    logging.critical('PGO包含特别说明 无法自动生成')
                    # 记录LOG
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'instruction', pgo.instruction, '',
                                  '',
                                  '', 'YES', 'PGO包含特别说明 无法自动生成')
                    is_can_auto = False
                    continue
                if is_can_auto:
                    for pgi in pgo.get_items:
                        try:
                            lens = PgProduct.objects.get(sku=pgi.lens_sku)
                            if bool(pgi.is_has_imgs):
                                logging.critical('包含图片 无法自动生成')
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', str(pgi.id), pgi.order_number, '自动下单', 'is_has_imgs',
                                              str(pgi.is_has_imgs), '', '', '', 'YES', '包含图片 无法自动生成')

                                is_can_auto = False
                                break
                            if not pgi.instruction == '' and not pgi.instruction == 'null' and pgi.instruction is not None:
                                logging.critical('行数据包含特别说明 无法自动生成')
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', str(pgi.id), pgi.order_number, '自动下单', 'instruction',
                                              str(pgi.instruction), '', '', '', 'YES', '行数据包含特别说明 无法自动生成')

                                is_can_auto = False
                                break

                            if lens.is_rx_lab:
                                logging.critical('车房片转入车房片判断方法')
                                # 转入车房片判断并生成LBO的分支
                                self.__rx_orders_handel(pgo)
                                is_can_auto = False
                                break
                            # 库存单单光验证
                            is_can_auto = self.__single_vision(pgi)

                        except Exception as e:
                            logging.critical(str(e))
                            is_can_auto = False
                            if self.write_log:
                                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e),
                                          'NO', '164异常报错')
                                logging.critical('generate lab orders completed ....')
                            break

                if is_can_auto:
                    self.__generate_lab_orders_address_verify(pgo, '')
                else:
                    logging.critical('验证规则未通过或进入车房处理')
        except Exception as e:
            logging.critical(str(e))
            if self.write_log:
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO', '177异常报错')
                logging.critical('generate lab orders completed ....')

    # 生成订单并校验地址
    def __generate_lab_orders_address_verify(self, pgo, comments):

        ailog = ai_log_control()  # AI操作日志

        pgo.status_control = 'AI'
        pgo.comments = comments
        pgo.save()
        # 写入LOG
        if self.write_log:
            ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单-生成工厂订单', 'comments',
                      comments, '', '', '', 'YES', '写入备注')

        try:
            for pgi in pgo.get_items:
                pgi.comments_inner = comments
                pgi.save()
                # 写入LOG
                if self.write_log:
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-生成工厂订单', 'comments',
                              comments, '', '', '', 'YES', '写入备注')

        except Exception as e:
            logging.critical(str(e))
            if self.write_log:
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO', '205异常报错')

        poc = PgOrderController()
        res = poc.generate_lab_orders(pgo.order_number)
        # 写入LOG
        if self.write_log:
            ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单-生成工厂订单', 'res',
                      res, '', '', '', 'YES', '生成工厂订单')

        logging.critical(res)

        # 地址校验
        ods = []
        ods.append(pgo.order_number)
        poc = PgOrderController()
        res = poc.pgorder_address_verified(ods)
        logging.critical(res)

    # 库存单单光验证
    def __single_vision(self, pgi):

        ailog = ai_log_control()  # AI操作日志

        pre = pgi.get_prescritpion
        # pre = Prescription()
        if abs(float(pre.rcyl)) > 2.00 or abs(float(pre.lcyl)) > 2.00:
            logging.critical('散光度高于200 无法自动生成')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'cyl',
                          'od_%s' % str(pre.rcyl), 'os_%s' % str(pre.lcyl), '', '', 'YES', '散光度高于200 不过')
            return False

        if float(pre.radd) > 0 or float(pre.ladd) > 0:
            logging.critical('验光单包含ADD 无法自动生成')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'add',
                          'od_%s' % str(pre.radd), 'os_%s' % str(pre.ladd), '', '', 'YES', '验光单包含ADD 不过')

            return False

        if float(pre.rpri) > 0 or float(pre.lpri) > 0:
            logging.critical('验光单包含PRISM 无法自动生成')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'PRISM',
                          'od_%s' % str(pre.rpri), 'os_%s' % str(pre.lpri), '', '', 'YES', '验光单包含PRISM 不过')

            return False

        if float(pre.rpri1) > 0 or float(pre.lpri1) > 0:
            logging.critical('验光单包含PRISM1 无法自动生成')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'PRISM1',
                          'od_%s' % str(pre.rpri1), 'os_%s' % str(pre.rpri1), '', '', 'YES', '验光单包含PRISM1 不过')

            return False

        if pre.used_for is not None and not pre.used_for == '':
            logging.critical('验光单包含 Used For 无法自动生成')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'Used For',
                          pre.used_for, '', '', '', 'YES', '验光单包含Used For 不过')

            return False

        return True

    # 狭义渐进单处理方法,不包括平顶双光
    def __progressive_handle(self, pgi):

        ailog = ai_log_control()  # AI操作日志

        seg_height = 0  # 加工瞳高
        standard_seg_hight = 0.5 * float(pgi.lens_height) + 3
        # 有鼻托
        if int(pgi.is_has_nose_pad) == 1:
            # 桥长大于20
            if float(pgi.bridge) > 20:
                # 框高小于等于30
                if float(pgi.lens_height) <= 30:
                    seg_height = standard_seg_hight
                else:
                    seg_height = 0.5 * float(pgi.lens_height) + 4
            # 桥长小于等于20
            else:
                seg_height = standard_seg_hight
        # 无鼻托
        else:
            # 桥大于20
            if float(pgi.bridge) > 20:
                seg_height = 0.5 * float(pgi.lens_height) + 5
            # 桥小于等于20
            else:
                # 框高小于等于37
                if float(pgi.lens_height) <= 37:
                    seg_height = standard_seg_hight
                else:
                    if float(pgi.lens_height) <= 43:
                        seg_height = 0.5 * float(pgi.lens_height) + 4
                    else:
                        seg_height = 0.5 * float(pgi.lens_height) + 5
        # 因为直接取PGI的pupils_position为0，所以重新查询一遍
        pgi_positions = PgOrderItem.objects.filter(order_number=pgi.order_number).values('pupils_position')
        pgi_position = pgi_positions[0]
        v_pgi_position = pgi_position['pupils_position']
        # 记录LOG
        if self.write_log:
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                      str(seg_height), '用户选：' + str(pgi.pupils_position), '二次查询结果=' + str(v_pgi_position), '', 'YES',
                      '计算狭义渐进瞳高，不写入PGI')

        # 根据用户习惯修正瞳高
        diff_lab_seg_hight_and_std = seg_height - standard_seg_hight  # 加工瞳高和标准瞳高差值
        # 用户选3
        if v_pgi_position == 3:
            seg_height = seg_height + 1
            diff_lab_seg_hight_and_std = seg_height - standard_seg_hight
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                          '用户选：' + str(v_pgi_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，计算结果')
        # 用户选1
        if v_pgi_position == 1:
            # 不是标准瞳高时修改，否则不修改
            if not diff_lab_seg_hight_and_std == 0:
                seg_height = seg_height - 1
                diff_lab_seg_hight_and_std = seg_height - standard_seg_hight
                # 记录LOG
                if self.write_log:
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                              '用户选：' + str(v_pgi_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，计算结果')
        # 生成加工要求
        ass_str = 'STD'
        if not diff_lab_seg_hight_and_std == 0:
            ass_str = 'STD+' + str(diff_lab_seg_hight_and_std)
        # 加工瞳高写入pgorderitem,并写入备注
        pgi.lab_seg_height = seg_height
        pgi.assemble_height = ass_str
        pgi.comments += '加工瞳高%smm;' % seg_height
        pgi.save()
        # 记录LOG
        if self.write_log:
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                      '用户选：' + str(v_pgi_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，写入PGI')
        # 通道选择，渐进单
        if pgi.lens_height == 30:  # 框高等于 30
            pgi.channel = 'FH15'
            pgi.comments += '车房加工采用短通道(7mm);'
            pgi.save()
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lens_height',
                          pgi.lens_height, 'FH15', '加备注：车房加工采用短通道(7mm)', '', 'YES', '通道选择，渐进单')

    # 平顶双光计算子镜高度方法
    def __flat_double_light_handle(self, pgi):
        ailog = ai_log_control()  # AI操作日志
        sub_mirrors_height = 0  # 子镜高度
        # 有鼻托
        if int(pgi.is_has_nose_pad) == 1:
            # 桥长大于20
            if float(pgi.bridge) > 20:
                if float(pgi.lens_height) <= 30:  # 框高小于等于30
                    sub_mirrors_height = 0.5 * float(pgi.lens_height) - 3
                else:
                    sub_mirrors_height = 0.5 * float(pgi.lens_height) - 2
            else:
                sub_mirrors_height = 0.5 * float(pgi.lens_height) - 3
        # 无鼻托
        else:
            # 桥长大于20
            if float(pgi.bridge) > 20:
                sub_mirrors_height = 0.5 * float(pgi.lens_height) - 1
            else:
                if float(pgi.lens_height) <= 37:  # 框高小于等于37
                    sub_mirrors_height = 0.5 * float(pgi.lens_height) - 3
                else:
                    sub_mirrors_height = 0.5 * float(pgi.lens_height) - 2
        # 超出范围按最大值算
        if sub_mirrors_height < 13:
            sub_mirrors_height = 13
        if sub_mirrors_height > 19:
            sub_mirrors_height = 19
        # 子镜高度写入PGI，并写入备注
        pgi.sub_mirrors_height = sub_mirrors_height
        pgi.comments += '子镜高度%smm;' % sub_mirrors_height
        pgi.save()
        # 记录LOG
        if self.write_log:
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sub_mirrors_height',
                      str(sub_mirrors_height), '', '', '', 'YES', '计算子镜高度，写入PGI')

    # 带有车房单的订单验证处理
    def __rx_orders_handel(self, pgo):
        logging.critical('开始 车房单审单')
        ailog = ai_log_control()

        is_can_auto = True
        progressive_num = 0  # 渐进单数量
        comments = ''  # 备注
        # 判断有无历史单查找历史单
        order_history = PgOrder.objects.filter(customer_id=pgo.customer_id, id__lt=pgo.id).only(
            'order_number').order_by('-id')[:5]
        if len(order_history) > 0:  # 有历史单数据
            logging.critical('有历史单，不过')
            # 记录LOG
            if self.write_log:
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'order_history',
                          order_history[0].order_number, '', '', '', 'YES', '有历史单，不过')

            return False

        # 重新遍历这个pgo，来做判断
        for pgi in pgo.get_items:
            try:
                lens = PgProduct.objects.get(sku=pgi.lens_sku)

                # 如果不是车房单
                if not lens.is_rx_lab:
                    is_can_auto = self.__single_vision(pgi)  # 单光验证
                    if not is_can_auto:  # 如果有库存单单光验证未通过，直接跳出
                        break
                # 是车房单
                else:
                    # 只有渐进片更新PGI的pupils_position和pupils_position_name
                    self.__update_pgi_pp(pgi)

                    # pgi = PgOrderItem()
                    # 如果是渐进，记录数量
                    if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:
                        progressive_num += 1
                        iteam_id_str = ''
                        iteam_id_str += ',%s' % pgi.item_id
                        # 一单中渐进数量大于1
                        if progressive_num > 1:
                            logging.critical('渐进单数量大于1 不过')
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'item_id',
                                          iteam_id_str, '', '', '', 'YES', '渐进单数量大于1 不过')
                            is_can_auto = False
                            break
                    # 车房单光和渐进都做以下验证
                    # 偏光镜
                    if bool(re.search('polarized', pgi.lens_name, re.IGNORECASE)):  # 平顶双光，计算子镜高度
                        logging.critical('偏光镜不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'lens_name',
                                      pgi.lens_name, '', '', '', 'YES', '偏光镜不过')

                        is_can_auto = False
                        break
                    # 有棱镜不过
                    if float(pgi.od_prism) > 0 or float(pgi.os_prism) > 0:
                        logging.critical('有棱镜不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'prism',
                                      'od_%s' % pgi.od_prism, 'os_%s' % pgi.os_prism, '', '', 'YES', '有棱镜不过')

                        is_can_auto = False
                        break
                    if float(pgi.od_prism1) > 0 or float(pgi.os_prism1) > 0:
                        logging.critical('有棱镜不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'prism1',
                                      'od_%s' % pgi.od_prism1, 'os_%s' % pgi.os_prism1, '', '', 'YES', '有棱镜1不过')
                        is_can_auto = False
                        break
                    # 单一瞳距
                    if pgi.is_singgle_pd == '1':
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单',
                                      'what_pd=' + pgi.is_singgle_pd,
                                      'pd_%s' % pgi.pd, '', '', '', 'YES', '成人镜框，瞳距小于等于45或大于75 不过')
                        # 儿童
                        if pgi.frame[0] == '3':
                            if float(pgi.pd) <= 40:
                                logging.critical('儿童镜框瞳距小于等于40 不过')
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                              'pd_%s' % pgi.pd, '', '', '', 'YES', '儿童镜框瞳距小于等于40 不过')

                                is_can_auto = False
                                break
                        # 成年人
                        else:
                            if float(pgi.pd) <= 45 or float(pgi.pd) > 75:
                                logging.critical('成人镜框，瞳距小于等于45或大于75 不过')
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                              'pd_%s' % pgi.pd, '', '', '', 'YES', '成人镜框，瞳距小于等于45或大于75 不过')

                                is_can_auto = False
                                break
                    # 双瞳距
                    else:
                        if abs(abs(pgi.od_pd) - abs(pgi.os_pd)) >= 5:
                            logging.critical('双瞳距，左右瞳距差大于等于5 不过')
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                          'od_pd_%s' % pgi.od_pd, 'os_pd_%s' % pgi.os_pd, '', '', 'YES',
                                          '双瞳距，左右瞳距差大于等于5 不过')
                            is_can_auto = False
                            break
                    # 左右ADD不同
                    if not pgi.os_add == pgi.od_add:
                        logging.critical('左右ADD不同  不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'add',
                                      'od_add_%s' % pgi.od_add, 'os_add_%s' % pgi.os_add, '', '', 'YES', '左右ADD不同  不过')
                        is_can_auto = False
                        break
                    # 度数差大于500
                    if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 5.0:
                        logging.critical('两眼度数差大于等于500 不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'sph',
                                      'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                                      '两眼度数差大于等于500 不过')
                        is_can_auto = False
                        break
                    # 散光差大于500
                    if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 5.0:
                        logging.critical('两眼散光差大于等于500 不过')
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'cyl',
                                      'od_add_%s' % pgi.od_cyl, 'os_add_%s' % pgi.os_cyl, '', '', 'YES',
                                      '两眼散光差大于等于500 不过')
                        is_can_auto = False
                        break
            except Exception as e:
                logging.critical(str(e))
                if self.write_log:
                    ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO',
                              '551异常报错')
        # 上面验证都通过才做以下处理
        if is_can_auto:
            # 重新遍历这个pgo,来做处理,不区分渐进与单光
            for pgi in pgo.get_items:
                try:
                    # 做处理,不区分渐进与单光
                    if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 3.0:
                        logging.critical('左右眼度数差大于等于300 添加备注及特殊说明')
                        pgi.special_handling = '注意平衡配重'
                        pgi.comments += '注意平衡配重;'
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sph',
                                      'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                                      '左右眼度数差大于等于300 添加备注及特殊说明')
                    if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 3.0:
                        logging.critical('左右眼散光差大于等于300 添加备注及特殊说明')
                        pgi.special_handling = '注意平衡配重'
                        pgi.comments += '注意平衡配重;'
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'cyl',
                                      'od_add_%s' % pgi.od_cyl, 'os_add_%s' % pgi.os_cyl, '', '', 'YES',
                                      '左右眼散光差大于等于300 添加备注及特殊说明')
                    if pgi.tint_sku[:2] == 'TS':
                        logging.critical('实色染色85% 添加备注及特殊说明')
                        pgi.special_handling = pgi.special_handling + '实色染色85%;'
                        pgi.comments += '实色染色85%;'
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.tint_sku, '', '', '', 'YES',
                                      '实色染色85% 添加备注及特殊说明')
                    if pgi.tint_sku[:2] == 'TG':
                        logging.critical('渐变染色70% 添加备注及特殊说明')
                        pgi.special_handling = pgi.special_handling + '渐变染色70%;'
                        pgi.comments += '渐变染色70%;'
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.tint_sku, '', '', '', 'YES',
                                      '渐变染色70% 添加备注及特殊说明')
                    # 设计加备注
                    if not pgi.pal_design_name == '' and pgi.pal_design_name is not None:
                        design_comments = ''
                        if pgi.pal_design_name == 'No Line Computer Progressive':
                            design_comments = '车房采用 办公设计1.3米 渐进设计;'
                        elif pgi.pal_design_name == 'No Line Office Progressive':
                            design_comments = '车房采用 办公设计4米 渐进设计;'
                        elif pgi.pal_design_name == 'Easy Adapt Progressive':
                            design_comments = '车房采用 IOT Alpha S35 渐进设计;'
                        elif pgi.pal_design_name == 'Drive Progressive':
                            design_comments = '车房采用 IOT Drive Progressive 渐进设计;'
                        elif pgi.pal_design_name == 'Sport Progressive':
                            design_comments = '车房采用 IOT Sport Progressive 渐进设计;'
                        elif pgi.pal_design_name == 'Premium Progressive':
                            design_comments = '车房采用 IOT Alpha H45 渐进设计;'
                        elif pgi.pal_design_name == 'Mobile Enhanced Progressive':
                            design_comments = '车房采用 IOT Alpha Mobile 渐进设计;'
                        elif pgi.pal_design_name == 'Near Enhanced Progressive':
                            design_comments = '车房采用 IOT Alpha H25 渐进设计;'
                        else:
                            design_comments = ''
                        pgi.comments += design_comments
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.pal_design_sku, pgi.pal_design_name, design_comments, '', 'YES',
                                      '设计加备注')
                    # 做处理，根据框型瞳高修正,区分广义渐进与单光
                    if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:  # 广义渐进
                        if bool(re.search('Lined Bifocal', pgi.lens_name, re.IGNORECASE)):
                            self.__flat_double_light_handle(pgi)  # 平顶双光处理
                        else:  # 狭义渐进，计算瞳高
                            self.__progressive_handle(pgi)  # 狭义渐进处理
                    else:  # 单光给出瞳高并添加备注
                        pgi.lab_seg_height = 0.5 * float(pgi.lens_height) + 4
                        pgi.assemble_height = 'STD+1.0'
                        pgi.comments += '加工瞳高%smm;' % str(0.5 * float(pgi.lens_height) + 4)
                        pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'assemble_height',
                                      str(pgi.lab_seg_height), '', '', '', 'YES', '非渐进给出瞳高')

                except Exception as e:
                    logging.critical(str(e))
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO',
                                  '646异常报错')
        # 生成工厂订单
        if is_can_auto:
            self.__generate_lab_orders_address_verify(pgo, comments)
        else:
            logging.critical('车房单验证规则未通过')

    # 更新PGI的pupils_position和pupils_position_name
    def __update_pgi_pp(self, pgi):
        ailog = ai_log_control()
        dict_poi = {
            "order_entity": pgi.pg_order_entity.base_entity,
            "profile_entity": pgi.profile_id,
            "order_item_entity": pgi.item_id,
            "profile_prescription_entity": pgi.profile_prescription_id,
            "prescription_entity": pgi.prescription_id
        }
        poc = PgOrderController()
        rb = poc.get_order_image(dict_poi)
        try:
            if rb.code == 0:
                body = rb.body
                pgi.pupils_position = body['pupils_position']
                pgi.pupils_position_name = body['pupils_position_name']
                pgi.save()

                # entity_pgis.order_image_urls = json.dumps(body['image_urls'])
        except Exception as e:
            logging.exception('exception: %s' % str(e))
            if self.write_log:
                ailog.add('pgorder', str(pgi.id), pgi.order_number, '自动下单', '', '', '', '-1', str(e), 'NO',
                          '677异常报错')
