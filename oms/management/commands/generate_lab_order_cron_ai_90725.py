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
    write_log = True  # 记录LOG 的开关
    # 渐进单数量
    progressive_num = 0
    pgitem_list = []

    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')
        '''
            81001:增加对订单中包含特别说明或包含测试用的COUPON_CODE的过滤
            81008:修复订单中包含特别说明，影响其他单光订单下单的BUG
        '''
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
            2019.07.25 --by gaoyu
            Django查询，取pupils_position时大多数为0
            所以把Django查询换成sql查询
            逻辑重写
        '''
        '''
            代码逻辑从新调整
        '''
        ailog = ai_log_control()  # AI操作日志

        try:
            # 查找生成1小时以上的PgOrder，approved不审，REVIEWED不审
            with connections["pg_oms_query"].cursor() as cursor:
                sql = '''
                    select id,order_number,is_inst,coupon_code,instruction,customer_id,base_entity
                    from oms_pgorder
                    where is_enabled = 1
                    and is_inlab = 0
                    and status = 'processing'
                    and TIMESTAMPDIFF(hour,CONVERT_TZ(create_at,'+0:00','+8:00'),CURRENT_TIMESTAMP) > 0
                    and status_control not in('APPROVED', 'REVIEWED', 'AI', 'MANUAL')
                '''
                cursor.execute(sql)
                pgos = namedtuplefetchall(cursor)

            for pgo in pgos:
                logging.critical('order_number %s' % pgo.order_number)
                self.progressive_num = 0
                is_can_auto = True
                # check pgorder
                is_can_auto_pg_flag = self.__check_pgorder(pgo, ailog)
                logging.critical('is_can_auto_pg_flag %s' % is_can_auto_pg_flag)
                if is_can_auto_pg_flag:
                    # 设置pgorder status_control 为MANUAL
                    self.__update_pgorder_status(pgo.order_number)
                    continue

                # PGO 对应的 pgi
                with connections["pg_oms_query"].cursor() as cursor:
                    sql = '''
                             SELECT * FROM oms_pgorderitem WHERE order_number = "%s" and attribute_set_name in ('Glasses', 'Goggles') 
                        ''' % pgo.order_number
                    cursor.execute(sql)
                    pgis = namedtuplefetchall(cursor)
                    if len(pgis) > 0:
                        for pgi in pgis:
                            try:
                                # check PgorderItem
                                is_can_auto_pgorderitem_flag = self.__check_pgorderitems(pgi, ailog)
                                logging.critical('is_can_auto_pgorderitem_flag %s' % is_can_auto_pgorderitem_flag)
                                if is_can_auto_pgorderitem_flag:
                                    # 设置pgorder status_control 为MANUAL
                                    self.__update_pgorder_status(pgi.order_number)
                                    is_can_auto = False
                                    break

                                # check PgProduct
                                lens_is_rx_lab = self.__check_pgproduct(pgi)
                                logging.critical('lens_is_rx_lab %s' % lens_is_rx_lab)
                                if lens_is_rx_lab == 'is_rx_lab':
                                    is_img_url = self.__update_pgi_pp(pgo.base_entity, pgi)
                                    # if is_img_url:
                                    #     # 设置pgorder status_control 为MANUAL
                                    #     self.__update_pgorder_status(pgi.order_number)
                                    #     is_can_auto = False
                                    #     break
                                    is_can_auto_flag = self.__garage_check(pgo, pgi, ailog)
                                elif lens_is_rx_lab == 'no_is_rx_lab':
                                    is_can_auto_flag = self.__single_vision(pgi)  # 单光验证
                                else:
                                    is_can_auto = False
                                    self.__update_pgorder_status(pgi.order_number)
                                    ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单', 'comments',
                                            'PgProduct产品未找到对应关系', '', '', '', 'YES', '写入备注')
                                    break

                                if is_can_auto_flag:
                                    # 设置pgorder status_control 为MANUAL
                                    self.__update_pgorder_status(pgi.order_number)
                                    is_can_auto = False
                                    break

                            except Exception as e:
                                self.__update_pgorder_status(pgi.order_number)
                                logging.critical('generate lab orders completed （%s）' % e)
                                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e),
                                          'NO', '142异常报错')
                                logging.critical('generate lab orders completed ....')
                                is_can_auto = False
                                break
                    else:
                        is_can_auto = True
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'comments', '订单是nRX订单', '', '', '',
                                  'YES', '订单是nRX订单')

                    # 生成laborder
                    if is_can_auto:
                        for pg_item in pgis:
                            # 添加备注
                            self.__add_comments(pg_item, ailog)
                        self.__generate_lab_orders_address_verify(pgo)
                    else:
                        logging.critical('验证规则未通过')

        except Exception as e:
            logging.critical("=================================>")
            logging.critical(str(e))
            logging.critical("=================================>")
            ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO', '155异常报错')
            logging.critical('generate lab orders completed ....')

    # 生成订单并校验地址
    def __generate_lab_orders_address_verify(self, pgo):
        try:
            ailog = ai_log_control()  # AI操作日志
            # 接口验证hold
            res_data = self.__check_hold_api(pgo.order_number)
            if res_data['flag']:
                # Django获取pgo对象
                entity_pgos = PgOrder.objects.filter(id=pgo.id)
                entity_pgo = entity_pgos[0]
                entity_pgo.status_control = 'AI'
                # 写入LOG
                if self.write_log:
                    ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单-生成工厂订单', 'comments',
                              entity_pgo.comments, '', '', '', 'YES', '写入备注')

                poc = PgOrderController()
                res = poc.generate_lab_orders(pgo.order_number)
                # 写入LOG
                if self.write_log:
                    ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单-生成工厂订单', 'res',
                              res, '', '', '', 'YES', '生成工厂订单')
                logging.critical(res)

                # 调用approve接口设置megento订单为初审完成状态
                if res == 'Success':
                    entity_pgo.is_inlab = True
                    entity_pgo.save()
                    post_order_comment_v2(pgo.base_entity, 'PG_ORDER_REVIEWED', 'processing', pgo.create_at)
                # 地址校验
                ods = []
                ods.append(pgo.order_number)
                poc = PgOrderController()
                res = poc.pgorder_address_verified(ods)
                logging.critical(res)
            else:
                self.__update_pgorder_status(pgo.order_number)
                ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单-生成工厂订单', 'comments',
                          res_data['comment'], '', '', '', 'YES', '写入备注')
        except Exception as e:
            pass


    # 库存单单光验证
    def __single_vision(self, pgi):
        ailog = ai_log_control()  # AI操作日志
        if float(pgi.od_add) != 0 or float(pgi.os_add) != 0:
            ailog.add('pgorderitem', str(pgo.id), pgi.order_number, '自动下单', 'item_id',
                      pgi.item_id, '', '', '', 'YES', 'lens_name 中不包含Progressive或者Bifocal 而add不为0 不过')
            return True

        if abs(float(pgi.os_cyl)) > 2.00 or abs(float(pgi.od_cyl)) > 2.00:
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'cyl',
                          'od_%s' % str(pgi.os_cyl), 'os_%s' % str(pgi.od_cyl), '', '', 'YES', '散光度高于200 不过')
            return True

        if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'add',
                          'od_%s' % str(pgi.od_add), 'os_%s' % str(pgi.os_add), '', '', 'YES', '验光单包含ADD 不过')
            return True

        if float(pgi.od_prism) > 0 or float(pgi.os_prism) > 0:
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'PRISM',
                          'od_%s' % str(pgi.od_prism), 'os_%s' % str(pgi.os_prism), '', '', 'YES', '验光单包含PRISM 不过')
            return True

        if float(pgi.od_prism1) > 0 or float(pgi.os_prism1) > 0:
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'PRISM1',
                          'od_%s' % str(pgi.od_prism1), 'os_%s' % str(pgi.os_prism1), '', '', 'YES', '验光单包含PRISM1 不过')
            return True

        if pgi.used_for is not None and not pgi.used_for == '' \
                and not pgi.used_for == 'READING' and not pgi.used_for == 'DISTANCE':
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'Used For',
                          pgi.used_for, '', '', '', 'YES', '验光单包含Used For 不过')
            return True
        #判断是否是平光眼镜
        if not pgi.is_nonPrescription:
            # 单一瞳距
            if pgi.is_singgle_pd == 1:
                # 儿童镜框
                if pgi.frame[0] == '3':
                    if float(pgi.pd) <= 40:
                        ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                  'pd_%s' % pgi.pd, '', '', '', 'YES', '儿童镜框瞳距小于等于40 不过')
                        return True
                # 成人镜框
                else:
                    if float(pgi.pd) <= 45 or float(pgi.pd) > 75:
                        ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                  'pd_%s' % pgi.pd, '', '', '', 'YES', '成人镜框，瞳距小于等于45或大于75 不过')
                        return True
            # 双瞳距
            else:
                # PD差大于5
                if abs(abs(pgi.od_pd) - abs(pgi.os_pd)) >= 5:
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                              'od_pd_%s' % pgi.od_pd, 'os_pd_%s' % pgi.os_pd, '', '', 'YES',
                              '双瞳距，左右瞳距差大于等于5 不过')
                    return True

                # PD和不在范围内
                sum_pd = abs(pgi.od_pd) + abs(pgi.os_pd)
                if sum_pd <= 45 or sum_pd > 75:
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                              'sum_pd_%s' % sum_pd, '', '', '', 'YES', '成人镜框，双瞳距小于等于45或大于75 不过')
                    return True


            # 度数差大于500
            if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 5.0:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'sph',
                          'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                          '两眼度数差大于等于500 不过')
                return True

        return False

    # 狭义渐进单处理方法,不包括平顶双光
    def __progressive_handle(self, pgi):

        ailog = ai_log_control()  # AI操作日志

        seg_height = 0  # 加工瞳高
        standard_seg_hight = 0.5 * float(pgi.lens_height) + 3
        # 有鼻托
        if pgi.is_has_nose_pad:
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

        # 根据用户习惯修正瞳高
        diff_lab_seg_hight_and_std = seg_height - standard_seg_hight  # 加工瞳高和标准瞳高差值
        # 用户选3
        if pgi.pupils_position == 3:
            seg_height = seg_height + 1
            diff_lab_seg_hight_and_std = seg_height - standard_seg_hight
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                          '用户选：' + str(pgi.pupils_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，计算结果')
        # 用户选1
        if pgi.pupils_position == 1:
            # 不是标准瞳高时修改，否则不修改
            if not diff_lab_seg_hight_and_std == 0:
                seg_height = seg_height - 1
                diff_lab_seg_hight_and_std = seg_height - standard_seg_hight
                # 记录LOG
                if self.write_log:
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                              '用户选：' + str(pgi.pupils_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，计算结果')

        # 生成加工要求
        ass_str = 'STD'
        if not diff_lab_seg_hight_and_std == 0:
            ass_str = 'STD+' + str(diff_lab_seg_hight_and_std)

        # Django取出对象保存
        entity_pgis = PgOrderItem.objects.filter(id=pgi.id)
        entity_pgi = entity_pgis[0]
        #20200811
        #entity_pgi.comments += '加工瞳高%smm;' % seg_height
        entity_pgi.lab_seg_height = str(seg_height)
        entity_pgi.assemble_height = ass_str
        entity_pgi.save()
        # 记录LOG
        if self.write_log:
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lab_seg_height',
                      '用户选：' + str(pgi.pupils_position), str(seg_height), '', '', 'YES', '根据用户选择调整狭义渐进瞳高，写入PGI')

        # 通道选择，渐进单
        if pgi.lens_height == 30:  # 框高等于 30
            entity_pgi.channel = 'FH15'
            entity_pgi.comments += '车房加工采用短通道(7mm);'
            entity_pgi.save()
            # 记录LOG
            if self.write_log:
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'lens_height',
                          pgi.lens_height, 'FH15', '加备注：车房加工采用短通道(7mm)', '', 'YES', '通道选择，渐进单')

    # 平顶双光计算子镜高度方法
    def __flat_double_light_handle(self, pgi):
        ailog = ai_log_control()  # AI操作日志
        sub_mirrors_height = 0  # 子镜高度
        # 有鼻托
        if pgi.is_has_nose_pad:
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
        # Django取出对象保存
        entity_pgis = PgOrderItem.objects.filter(id=pgi.id)
        entity_pgi = entity_pgis[0]
        #entity_pgi.comments += '子镜高度%smm;' % sub_mirrors_height
        entity_pgi.sub_mirrors_height = str(sub_mirrors_height)
        entity_pgi.save()
        # 记录LOG
        if self.write_log:
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sub_mirrors_height',
                      str(sub_mirrors_height), '', '', '', 'YES', '计算子镜高度，写入PGI')

    # 带有车房单的订单验证处理
    def __rx_orders_handel(self, pgo, pgis):
        logging.critical('开始 车房单审单')
        ailog = ai_log_control()  # 操作记录
        is_can_auto = True  # 通过标志
        # 需要写入的数据
        progressive_num = 0  # 渐进单数量

        # 保存 pgo的base_entity
        pgo_base_entity = pgo.base_entity
        # 重新遍历这个pgo，来做判断
        for pgi in pgis:
            try:
                lens = PgProduct.objects.get(sku=pgi.lens_sku)

                # 如果不是车房单
                if not lens.is_rx_lab:
                    is_can_auto = self.__single_vision(pgi)  # 单光验证
                    if not is_can_auto:  # 如果有库存单单光验证未通过，直接跳出
                        break
                # 是车房单
                else:
                    # 更新PGI的pupils_position和pupils_position_name
                    self.__update_pgi_pp(pgo_base_entity, pgi)

                    # 如果是渐进，记录数量,并更新字段
                    if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:
                        # 渐进单做历史单检查，存在历史单不过
                        order_history = PgOrder.objects.filter(customer_id=pgo.customer_id, id__lt=pgo.id).only(
                            'order_number').order_by('-id')[:5]
                        if len(order_history) > 0:  # 有历史单数据
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'order_history',
                                          order_history[0].order_number, '', '', '', 'YES', '有历史单，不过')
                            return False

                        progressive_num += int(pgi.quantity)
                        # 一单中渐进数量大于1
                        if progressive_num > 1:
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'item_id',
                                          pgi.item_id, '', '', '', 'YES', '渐进单数量大于1 不过')
                            is_can_auto = False
                            break

                    # 车房单光和渐进都做以下验证
                    # 有棱镜不过
                    if float(pgi.od_prism) > 0 or float(pgi.os_prism) > 0:
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
                    if pgi.is_singgle_pd == 1:

                        # 儿童镜框
                        if pgi.frame[0] == '3':
                            if float(pgi.pd) <= 40:
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                              'pd_%s' % pgi.pd, '', '', '', 'YES', '儿童镜框瞳距小于等于40 不过')
                                is_can_auto = False
                                break

                        # 成人镜框
                        else:
                            if float(pgi.pd) <= 45 or float(pgi.pd) > 75:
                                # 记录LOG
                                if self.write_log:
                                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                              'pd_%s' % pgi.pd, '', '', '', 'YES', '成人镜框，瞳距小于等于45或大于75 不过')
                                is_can_auto = False
                                break

                    # 双瞳距
                    else:
                        # PD差大于5
                        if abs(abs(pgi.od_pd) - abs(pgi.os_pd)) >= 5:
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                          'od_pd_%s' % pgi.od_pd, 'os_pd_%s' % pgi.os_pd, '', '', 'YES',
                                          '双瞳距，左右瞳距差大于等于5 不过')
                            is_can_auto = False
                            break

                        # PD和不在范围内
                        sum_pd = abs(pgi.od_pd) + abs(pgi.os_pd)
                        if sum_pd <= 45 or sum_pd > 75:
                            # 记录LOG
                            if self.write_log:
                                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                                          'sum_pd_%s' % sum_pd, '', '', '', 'YES', '成人镜框，双瞳距小于等于45或大于75 不过')
                            is_can_auto = False
                            break

                    # 左右ADD不同
                    if not pgi.os_add == pgi.od_add:
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'add',
                                      'od_add_%s' % pgi.od_add, 'os_add_%s' % pgi.os_add, '', '', 'YES', '左右ADD不同  不过')
                        is_can_auto = False
                        break

                    # 度数差大于500
                    if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 5.0:
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'sph',
                                      'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                                      '两眼度数差大于等于500 不过')
                        is_can_auto = False
                        break

                    # 散光差大于500
                    if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 5.0:
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
                              '512异常报错')

        # 上面验证都通过才做以下处理
        if is_can_auto:
            # 重新遍历这个pgo,来做处理,不区分渐进与单光
            for pgi in pgis:
                special_handling = ''  # 加工要求
                comments_item = ''  # 备注
                try:
                    # 做处理,不区分渐进与单光
                    if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 3.0:
                        special_handling += '注意平衡配重;'
                        comments_item += '注意平衡配重;'
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sph',
                                      'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                                      '左右眼度数差大于等于300 添加备注及特殊说明')

                    if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 3.0:
                        special_handling += '注意平衡配重'
                        comments_item += '注意平衡配重;'
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'cyl',
                                      'od_add_%s' % pgi.od_cyl, 'os_add_%s' % pgi.os_cyl, '', '', 'YES',
                                      '左右眼散光差大于等于300 添加备注及特殊说明')

                    if pgi.tint_sku[:2] == 'TS':
                        special_handling += '实色染色85%;'
                        comments_item += '实色染色85%;'
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.tint_sku, '', '', '', 'YES', '实色染色85% 添加备注及特殊说明')

                    if pgi.tint_sku[:2] == 'TG':
                        special_handling += '渐变染色70%;'
                        comments_item += '渐变染色70%;'
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.tint_sku, '', '', '', 'YES', '渐变染色70% 添加备注及特殊说明')

                    # 设计加备注
                    if not pgi.pal_design_name == '' and pgi.pal_design_name is not None:
                        if pgi.pal_design_name == 'No Line Computer Progressive':
                            comments_item += '车房采用 办公渐进1.3米;'
                        elif pgi.pal_design_name == 'No Line Office Progressive':
                            comments_item += '车房采用 办公渐进4米;'
                        elif pgi.pal_design_name == 'Easy Adapt Progressive':
                            comments_item += '车房采用 IOT渐进 Alpha S35;'
                        elif pgi.pal_design_name == 'Drive Progressive':
                            comments_item += '车房采用 IOT渐进 Outdoor DriveProgressive;'
                        elif pgi.pal_design_name == 'Sport Progressive':
                            comments_item += '车房采用 IOT渐进 Outdoor Sport Progressive;'
                        elif pgi.pal_design_name == 'Premium Progressive':
                            comments_item += '车房采用 IOT渐进 Alpha H45;'
                        elif pgi.pal_design_name == 'Mobile Enhanced Progressive':
                            comments_item += '车房采用 IOT渐进 Alpha Mobile;'
                        elif pgi.pal_design_name == 'Near Enhanced Progressive':
                            comments_item += '车房采用 IOT渐进 Alpha H25;'

                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                                      pgi.pal_design_sku, pgi.pal_design_name, comments_item, '', 'YES',
                                      '设计加备注')

                    # Django取出对象保存
                    entity_pgis = PgOrderItem.objects.filter(id=pgi.id)
                    entity_pgi = entity_pgis[0]
                    entity_pgi.comments += comments_item
                    entity_pgi.special_handling += special_handling
                    entity_pgi.save()

                    # 做处理，根据框型瞳高修正,区分广义渐进与单光
                    if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:  # 广义渐进
                        if bool(re.search('Bifocal', pgi.lens_name, re.IGNORECASE)):
                            self.__flat_double_light_handle(pgi)  # 平顶双光处理
                        else:  # 狭义渐进，计算瞳高
                            self.__progressive_handle(pgi)  # 狭义渐进处理
                    else:  # 单光给出瞳高并添加备注
                        entity_pgi.lab_seg_height = str(0.5 * float(pgi.lens_height) + 4)
                        entity_pgi.assemble_height = 'STD+1.0'
                        #20200811
                        #entity_pgi.comments += '加工瞳高%smm;' % str(0.5 * float(pgi.lens_height) + 4)
                        entity_pgi.save()
                        # 记录LOG
                        if self.write_log:
                            ailog.add('pgorderitem', entity_pgi.order_number, str(entity_pgi.item_id), '自动下单-处理',
                                      'assemble_height', str(entity_pgi.lab_seg_height), '', '', '', 'YES', '非渐进给出瞳高')

                except Exception as e:
                    logging.critical(str(e))
                    if self.write_log:
                        ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', '', '', '', '-1', str(e), 'NO',
                                  '608异常报错')

        # 生成工厂订单
        if is_can_auto:
            self.__generate_lab_orders_address_verify(pgo)
        else:
            logging.critical('车房单验证规则未通过')

    # 更新PGI的pupils_position和pupils_position_name
    def __update_pgi_pp(self, pgo_bese_entity, pgi):
        ailog = ai_log_control()
        condition_key = []
        condition_value = []
        is_img_url = False
        try:
            dict_poi = {
                "order_entity": pgo_bese_entity,
                "profile_entity": pgi.profile_id,
                "order_item_entity": pgi.item_id,
                "profile_prescription_entity": pgi.profile_prescription_id,
                "prescription_entity": pgi.prescription_id
            }
            poc = PgOrderController()
            rb = poc.get_order_image(dict_poi)
            if rb.code == 0:
                body = rb.body
                pgi_id = pgi.id
                pupils_position = body['pupils_position']
                ppupils_position_name = body['pupils_position_name']
                order_image_urls = body['image_urls']
                condition_key.append('`pupils_position`=%s')
                condition_value.append(pupils_position)
                condition_key.append('`pupils_position_name`=%s')
                condition_value.append(ppupils_position_name)
                if len(order_image_urls) > 0:
                    condition_key.append('`is_has_imgs`=%s')
                    condition_value.append(True)
                    is_img_url = True
                condition_value.append(pgi_id)
                with connections['default'].cursor() as cursor:
                    update_sql = ''' UPDATE oms_pgorderitem SET ''' + ','.join(condition_key) + ''' WHERE id="%s" ''' \
                                 % tuple(condition_value)
                    cursor.execute(update_sql)

            return is_img_url
        except Exception as e:
            ailog.add('pgorder', str(pgi.id), pgi.order_number, 'get_order_image', '', '', '', '-1', str(e), 'NO',
                      e)
            return is_img_url

    def __check_pgorder(self, pgo, ailog):
        if pgo.is_inst:
            ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'is_inst', str(pgo.is_inst), '', '',
                      '', 'YES', '包含特别说明 无法自动生成')
            return True

        if pgo.coupon_code == 'PG-INTERNAL':
            # 记录LOG
            ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'coupon_code', pgo.coupon_code, '',
                      '', '', 'YES', '内部测试订单 无法自动生成')
            return True

        if pgo.coupon_code:
            if bool(re.search('REPLACE', pgo.coupon_code, re.IGNORECASE)):
                # 记录LOG
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'coupon_code', pgo.coupon_code,
                          '', '', '', 'YES', '替换订单 无法自动生成')
                return True

        # 包含instruction不过
        if not pgo.instruction == '' and not pgo.instruction == 'null' and pgo.instruction is not None:
            ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'instruction', pgo.instruction, '',
                      '', '', 'YES', 'PGO包含特别说明 无法自动生成')
            return True

        return False

    def __check_pgorderitems(self, pgi, ailog):
        if pgi.is_has_imgs:
            ailog.add('pgorderitem', str(pgi.id), pgi.order_number, '自动下单', 'is_has_imgs',
                      str(pgi.is_has_imgs), '', '', '', 'YES', '包含图片 无法自动生成')
            return True

        if not pgi.instruction == '' and not pgi.instruction == 'null' and pgi.instruction is not None:
            ailog.add('pgorderitem', str(pgi.id), pgi.order_number, '自动下单', 'instruction',
                      str(pgi.instruction), '', '', '', 'YES', '行数据包含特别说明 无法自动生成')
            return True

        return False

    def __garage_check(self, pgo, pgi, ailog):
        if (bool(re.search('Bifocal', pgi.lens_name, re.IGNORECASE)) or
            bool(re.search('Progressives', pgi.lens_name, re.IGNORECASE))) \
                and (float(pgi.od_add) == 0 or float(pgi.os_add) == 0):
            ailog.add('pgorderitem', str(pgo.id), pgo.order_number, '自动下单', 'item_id',
                      pgi.item_id, '', '', '', 'YES', 'lens_name 中含有Progressive或者Bifocal 而add为0 不过')
            return True

        if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:
            # 渐进单做历史单检查，存在历史单不过
            order_history = PgOrder.objects.filter(customer_id=pgo.customer_id, id__lt=pgo.id).only(
                'order_number').order_by('-id')[:5]
            if len(order_history) > 0:  # 有历史单数据
                logging.critical('%s, %s' % (pgo.order_number, '有历史单，不过'))
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'order_history',
                          order_history[0].order_number, '', '', '', 'YES', '有历史单，不过')
                return True

            self.progressive_num += int(pgi.quantity)
            # 一单中渐进数量大于1
            if self.progressive_num > 1:
                logging.critical('%s, %s' % (pgo.order_number, '渐进单数量大于1 不过'))
                ailog.add('pgorder', str(pgo.id), pgo.order_number, '自动下单', 'item_id',
                          pgi.item_id, '', '', '', 'YES', '渐进单数量大于1 不过')
                return True

        if float(pgi.od_prism) > 0 or float(pgi.os_prism) > 0:
            logging.critical('%s, %s' % (pgo.order_number, '有棱镜不过'))
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'prism',
                      'od_%s' % pgi.od_prism, 'os_%s' % pgi.os_prism, '', '', 'YES', '有棱镜不过')
            return True

        if float(pgi.od_prism1) > 0 or float(pgi.os_prism1) > 0:
            logging.critical('%s, %s' % (pgo.order_number, '有棱镜1不过'))
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'prism1',
                      'od_%s' % pgi.od_prism1, 'os_%s' % pgi.os_prism1, '', '', 'YES', '有棱镜1不过')
            return True

        # 单一瞳距
        if pgi.is_singgle_pd == 1:
            # 儿童镜框
            if pgi.frame[0] == '3':
                if float(pgi.pd) <= 40:
                    logging.critical('%s, %s' % (pgo.order_number, '儿童镜框瞳距小于等于40 不过'))
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                              'pd_%s' % pgi.pd, '', '', '', 'YES', '儿童镜框瞳距小于等于40 不过')
                    return True
            # 成人镜框
            else:
                if float(pgi.pd) <= 45 or float(pgi.pd) > 75:
                    logging.critical('%s, %s' % (pgo.order_number, '成人镜框，瞳距小于等于45或大于75 不过'))
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                              'pd_%s' % pgi.pd, '', '', '', 'YES', '成人镜框，瞳距小于等于45或大于75 不过')
                    return True
        # 双瞳距
        else:
            # PD差大于5
            if abs(abs(pgi.od_pd) - abs(pgi.os_pd)) >= 5:
                logging.critical('%s, %s' % (pgo.order_number, '双瞳距，左右瞳距差大于等于5 不过'))
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                          'od_pd_%s' % pgi.od_pd, 'os_pd_%s' % pgi.os_pd, '', '', 'YES',
                          '双瞳距，左右瞳距差大于等于5 不过')
                return True

            # PD和不在范围内
            sum_pd = abs(pgi.od_pd) + abs(pgi.os_pd)
            if sum_pd <= 45 or sum_pd > 75:
                logging.critical('%s, %s' % (pgo.order_number, '成人镜框，双瞳距小于等于45或大于75 不过'))
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'pd',
                          'sum_pd_%s' % sum_pd, '', '', '', 'YES', '成人镜框，双瞳距小于等于45或大于75 不过')
                return True

        # 左右ADD不同
        if not pgi.os_add == pgi.od_add:
            logging.critical('%s, %s' % (pgo.order_number, '左右ADD不同  不过'))
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'add',
                      'od_add_%s' % pgi.od_add, 'os_add_%s' % pgi.os_add, '', '', 'YES', '左右ADD不同  不过')
            return True

        # 度数差大于500
        if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 5.0:
            logging.critical('%s, %s' % (pgo.order_number, '两眼度数差大于等于500 不过'))
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'sph',
                      'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                      '两眼度数差大于等于500 不过')
            return True

        # 散光差大于500
        if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 5.0:
            logging.critical('%s, %s' % (pgo.order_number, '两眼散光差大于等于500 不过'))
            ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单', 'cyl',
                      'od_add_%s' % pgi.od_cyl, 'os_add_%s' % pgi.os_cyl, '', '', 'YES',
                      '两眼散光差大于等于500 不过')
            return True

        return False

    def __check_pgproduct(self, pgi):
        lens = PgProduct.objects.filter(sku=pgi.lens_sku)
        if len(lens) > 0:
            lens_product = lens[0]
            if lens_product.is_rx_lab:
                return 'is_rx_lab'
            else:
                return 'no_is_rx_lab'
        else:
            return 'error'

    def __add_comments(self, pgi, ailog):
        # 做处理,不区分渐进与单光
        special_handling = ''  # 加工要求
        comments_item = ''  # 备注
        try:
            if abs(float(pgi.os_sph) - float(pgi.od_sph)) >= 3.0:
                special_handling += '注意平衡配重;'
                comments_item += '注意平衡配重;'
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sph',
                          'od_add_%s' % pgi.od_sph, 'os_add_%s' % pgi.os_sph, '', '', 'YES',
                          '左右眼度数差大于等于300 添加备注及特殊说明')

            if abs(float(pgi.os_cyl) - float(pgi.od_cyl)) >= 3.0:
                special_handling += '注意平衡配重'
                comments_item += '注意平衡配重;'
                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'cyl',
                          'od_add_%s' % pgi.od_cyl, 'os_add_%s' % pgi.os_cyl, '', '', 'YES',
                          '左右眼散光差大于等于300 添加备注及特殊说明')

            if pgi.tint_sku:
                if pgi.tint_sku[:2] == 'TS':
                    special_handling += '实色染色85%;'
                    comments_item += '实色染色85%;'
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                              pgi.tint_sku, '', '', '', 'YES', '实色染色85% 添加备注及特殊说明')

                if pgi.tint_sku[:2] == 'TG':
                    special_handling += '渐变染色70%;'
                    comments_item += '渐变染色70%;'
                    ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                              pgi.tint_sku, '', '', '', 'YES', '渐变染色70% 添加备注及特殊说明')

            # 设计加备注
            if not pgi.pal_design_name == '' and pgi.pal_design_name is not None:
                if pgi.pal_design_name == 'No Line Computer Progressive':
                    comments_item += '车房采用 办公渐进1.3米;'
                elif pgi.pal_design_name == 'No Line Office Progressive':
                    comments_item += '车房采用 办公渐进4米;'
                elif pgi.pal_design_name == 'Easy Adapt Progressive':
                    comments_item += '车房采用 IOT渐进 Alpha S35;'
                elif pgi.pal_design_name == 'Drive Progressive':
                    comments_item += '车房采用 IOT渐进 Outdoor DriveProgressive;'
                elif pgi.pal_design_name == 'Sport Progressive':
                    comments_item += '车房采用 IOT渐进 Outdoor Sport Progressive;'
                elif pgi.pal_design_name == 'Premium Progressive':
                    comments_item += '车房采用 IOT渐进 Alpha H45;'
                elif pgi.pal_design_name == 'Mobile Enhanced Progressive':
                    comments_item += '车房采用 IOT渐进 Alpha Mobile;'
                elif pgi.pal_design_name == 'Near Enhanced Progressive':
                    comments_item += '车房采用 IOT渐进 Alpha H25;'

                ailog.add('pgorderitem', pgi.order_number, str(pgi.item_id), '自动下单-处理', 'sku',
                          pgi.pal_design_sku, pgi.pal_design_name, comments_item, '', 'YES',
                          '设计加备注')

            if (float(pgi.od_add) > 0 and float(pgi.os_add) == 0) or (float(pgi.od_add) == 0 and float(pgi.os_add) > 0):
                comments_item += ';单眼ADD'

            # Django取出对象保存
            entity_pgi = PgOrderItem.objects.get(id=pgi.id)
            if entity_pgi.comments:
                old_comments = entity_pgi.comments
            else:
                old_comments = ''

            if entity_pgi.special_handling:
                old_special_handling = entity_pgi.special_handling
            else:
                old_special_handling = ''
            entity_pgi.comments = old_comments + comments_item
            entity_pgi.special_handling = old_special_handling + special_handling
            entity_pgi.save()

            # 做处理，根据框型瞳高修正,区分广义渐进与单光
            if float(pgi.od_add) > 0 or float(pgi.os_add) > 0:  # 广义渐进
                if bool(re.search('Bifocal', pgi.lens_name, re.IGNORECASE)):
                    self.__flat_double_light_handle(pgi)  # 平顶双光处理
                else:  # 狭义渐进，计算瞳高
                    self.__progressive_handle(pgi)  # 狭义渐进处理
            else:  # 单光给出瞳高并添加备注
                entity_pgi.lab_seg_height = str(0.5 * float(pgi.lens_height) + 4)
                entity_pgi.assemble_height = 'STD+1.0'
                #20200811
                #entity_pgi.comments += '加工瞳高%smm;' % str(0.5 * float(pgi.lens_height) + 4)
                entity_pgi.save()
                # 记录LOG
                if self.write_log:
                    ailog.add('pgorderitem', entity_pgi.order_number, str(entity_pgi.item_id), '自动下单-处理',
                              'assemble_height', str(entity_pgi.lab_seg_height), '', '', '', 'YES', '非渐进给出瞳高')

        except Exception as e:
            ailog.add('pgorder', str(pgi.id), pgi.order_number, '自动下单', '', '', '', '-1', str(e), 'NO',
                      '608异常报错')

    def __update_pgorder_status(self, order_number):
        pg = PgOrder.objects.get(order_number=order_number)
        pg.status_control = 'MANUAL'
        pg.save()

    def __check_hold_api(self, order_number):
        rm = {}
        comment = ''
        hold_flag = True
        check_dict = {}
        req=None
        try:
            with connections["pg_oms_query"].cursor() as cursor_check:
                check_sql = '''SELECT t0.base_entity AS order_id, t1.item_id AS item_id, 
                                      t1.profile_prescription_id AS prescription_id, t1.profile_id AS profile_id
                                FROM oms_pgorder AS t0 
                                LEFT JOIN oms_pgorderitem AS t1 
                                ON t0.order_number = t1.order_number 
                                WHERE t0.order_number="%s"''' % order_number
                cursor_check.execute(check_sql)
                check_list = namedtuplefetchall(cursor_check)
                for item in check_list:
                    value_list = []
                    if not item.order_id in check_dict.keys():
                        check_dict[str(item.order_id)] = []
                    item_id = int(item.item_id) if item.item_id else ''
                    prescription_id = int(item.prescription_id) if item.prescription_id else ''
                    profile_id = int(item.profile_id) if item.profile_id else ''
                    value_list.append(item_id)
                    value_list.append(prescription_id)
                    value_list.append(profile_id)
                    check_dict[item.order_id].append(value_list)

                json_string = json.dumps(check_dict)
                check_json = json.loads(json_string)
                http_headers = {
                    'Content-Type': 'application/json',
                    "Charset": "UTF-8"
                }
                # 设置重连次数
                requests.adapters.DEFAULT_RETRIES = 5
                s = requests.session()
                # 设置连接活跃状态为False
                s.keep_alive = False
                req = requests.post(url=settings.CHECK_ORDER_HOLD_URL, json=check_json, headers=http_headers,
                                    verify=False)
                resp = req.text
                logging.debug(resp)
                res_json = json.loads(resp)
                if res_json['code'] == 0:
                    for res in res_json['data']:
                        if res['code'] == 'true':
                            hold_flag = False
                            comment = res['connects']
                        break
                else:
                    hold_flag = False
                    comment = res_json['msg']

                rm['flag'] = hold_flag
                rm['comment'] = comment
                logging.debug(rm)
                return rm
        except Exception as e:
            hold_flag = False
            rm['flag'] = hold_flag
            rm['comment'] = e
            logging.debug(rm)
            return rm
        finally:
            # 关闭请求  释放内存
            req.close()
            del(req)