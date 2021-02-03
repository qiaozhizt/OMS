# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction
# Create your models here.
from oms.models.order_models import LabOrder
from oms.models import choices_models
from vendor.models import lens_order
import simplejson as json
import logging

from util.response import response_message
from oms.controllers.lab_order_controller import lab_order_controller
from api.controllers.tracking_controllers import tracking_lab_order_controller


class base_type(models.Model):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='BAMO', editable=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'SEQUENCE', default=0)
    is_enabled = models.BooleanField(u'IS Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)


class qc_base(base_type):
    class Meta:
        abstract = True

    laborder_id = models.IntegerField(u'Entity ID', default=0)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)

    laborder_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                        blank=True,
                                        null=True, editable=False)


class prescripiton_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='BAPB', editable=False)

    # Prescription
    profile_id = models.CharField(u'Profile ID', max_length=128, default='', null=True, blank=True)
    profile_name = models.CharField(u'Profile Name', max_length=255, default='', null=True,
                                    blank=True)
    profile_prescription_id = models.CharField(u'Profile Prescription ID', max_length=128, default='', null=True,
                                               blank=True)
    # jo-9
    prescription_id = models.CharField(u'prescription id', max_length=40, null=True, blank=True, default='')
    prescription_name = models.CharField(u'name', max_length=128, null=True, blank=True, default='')
    prescription_type = models.CharField(u'type', max_length=128, null=True, blank=True, default='',
                                         choices=choices_models.PRESCRIPTION_CHOICES)

    od_sph = models.DecimalField(u'sph(OD)', max_digits=5, decimal_places=2, default=0)
    od_cyl = models.DecimalField(u'cyl(OD)', max_digits=5, decimal_places=2, default=0)
    od_axis = models.DecimalField(u'axis(OD)', max_digits=5, decimal_places=0, default=0)
    os_sph = models.DecimalField(u'sph(OS)', max_digits=5, decimal_places=2, default=0)
    os_cyl = models.DecimalField(u'cyl(OS)', max_digits=5, decimal_places=2, default=0)
    os_axis = models.DecimalField(u'axis(OS)', max_digits=5, decimal_places=0, default=0)

    pd = models.DecimalField(u'pd', max_digits=5, decimal_places=1, default=0)
    is_singgle_pd = models.BooleanField(u'single pd', default=True)
    od_pd = models.DecimalField(u'pd(OD)', max_digits=5, decimal_places=1, default=0)
    os_pd = models.DecimalField(u'pd(OS)', max_digits=5, decimal_places=1, default=0)

    # Prescription extends

    od_add = models.DecimalField(u'add(OD)', max_digits=5, decimal_places=2, default=0)
    os_add = models.DecimalField(u'add(OS)', max_digits=5, decimal_places=2, default=0)

    od_prism = models.DecimalField(u'prism-H(OD)', max_digits=5, decimal_places=2, default=0)
    od_base = models.CharField(u'base-H(OD)', max_length=40, null=True, blank=True, default='',
                               choices=choices_models.BASE_CHOICES)

    od_prism1 = models.DecimalField(u'prism-V(OD)', max_digits=5, decimal_places=2, default=0)
    od_base1 = models.CharField(u'base-V(OD)', max_length=40, null=True, blank=True, default='',
                                choices=choices_models.BASE_CHOICES)

    os_prism = models.DecimalField(u'prism-H(OS)', max_digits=5, decimal_places=2, default=0)
    os_base = models.CharField(u'base-H(OS)', max_length=40, null=True, blank=True, default='',
                               choices=choices_models.BASE_CHOICES)

    os_prism1 = models.DecimalField(u'prism-V(OS)', max_digits=5, decimal_places=2, default=0)
    os_base1 = models.CharField(u'base-V(OS)', max_length=40, null=True, blank=True, default='',
                                choices=choices_models.BASE_CHOICES)

    used_for = models.CharField(u'used for', max_length=40, null=True, blank=True, default='',
                                choices=choices_models.USED_FOR_CHOICES)


class prescripiton_actual(prescripiton_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='BAPA', editable=False)


# 镜片来片登记
class lens_registration(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OLRT', editable=False)


# 镜片来片登记
class lens_registration_control:
    def add(self, request, lab_order_entity):
        rm = response_message()
        rm.code = -9
        rm.message = '准备操作'

        try:
            with transaction.atomic():
                logging.debug('开始进入 ...')
                logging.debug('没有重复记录')

                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_order_entity)

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]

                if not lbo == None:
                    objs = lens_registration.objects.all().order_by('-id')[:1]
                    if len(objs) > 0:
                        ob = objs[0]
                        if ob.lab_number == lbo.lab_number and \
                                lbo.status == 'LENS_REGISTRATION':
                            rm.code = -3
                            rm.message = '疑似重复操作'
                            return rm

                    if not lbo.status == 'PRINT_DATE' and not lbo.status == 'LENS_RETURN' \
                            and not lbo.status == 'GLASSES_RETURN' and not lbo.status == 'LENS_OUTBOUND' \
                            and not lbo.status == 'REQUEST_NOTES' and not lbo.status == 'FRAME_OUTBOUND':
                        rm.code = -4
                        rm.message = '只有订单处于镜片生产/镜片退货/成镜退货/镜片出库的状态时才可以执行来片登记; ' \
                                     '\n该订单当前状态为:{%s}' % lbo.get_status_display()
                        return rm

                    # VD 6 ,VD 8，lens_order为已出库状态才能来片登记
                    if lbo.vendor == '6' or lbo.vendor == '8':
                        los = lens_order.objects.filter(lab_number=lbo.lab_number)
                        for lo in los:
                            if not lo.status == 'LENS_OUTBOUND':
                                rm.code = -4
                                rm.message = '此订单未完成镜片出库'
                                return rm

                    obj = lens_registration()
                    obj.laborder_id = lbo.id
                    obj.lab_number = lbo.lab_number
                    obj.laborder_entity = lbo
                    obj.user_id = request.user.id
                    obj.user_name = request.user.username
                    obj.save()

                    lbo.status = 'LENS_REGISTRATION'
                    lbo.save()

                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'LENS_REGISTRATION')

                    rm.obj = obj
                    rm.code = 0
                    rm.message = '此操作已成功'
                else:
                    rm.code = -4
                    rm.message = '订单未找到'
                    return rm

        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)

        return rm


# 镜片初检记录
class preliminary_checking(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OLPC', editable=False)
    prescripiton_actual_entity = models.ForeignKey(prescripiton_actual, models.SET_NULL,
                                                   blank=True,
                                                   null=True, editable=False)
    is_qualified = models.BooleanField(u'IS Qualified', default=False)
    reason_code = models.CharField(u'原因代码', max_length=20, default='-1', null=True, blank=True)
    reason = models.CharField(u'原因', max_length=512, default='-1', null=True, blank=True)


class preliminary_checking_control:
    def add(self, request, lab_order_entity, qualified, reason_code, reason, act_lens_sku, act_lens_name):
        rm = response_message()
        rm.code = -9
        rm.message = '准备操作'

        try:
            logging.debug('开始进入 ...')
            logging.debug('没有重复记录')
            logging.debug('------------------------------------------------------------')
            logging.debug('lab entity: %s' % lab_order_entity)

            logging.debug('------------------------------------------------------------')
            # with transaction.atomic():
            loc = lab_order_controller()
            lbos = loc.get_by_entity(lab_order_entity)

            if len(lbos) == 0:
                rm.code = -20
                rm.message = "未找到订单记录,请求的订单号[%s]" % lab_order_entity
                return rm

            lbo = None
            if len(lbos) > 0:
                lbo = lbos[0]

            if not lbo == None:
                objs = preliminary_checking.objects.all().order_by('-id')[:1]
                if len(objs) > 0:
                    ob = objs[0]
                    if ob.lab_number == lbo.lab_number:
                        rm.code = -3
                        rm.message = '疑似重复操作'
                        return rm

                if not lbo.status == 'LENS_REGISTRATION':
                    rm.code = -4
                    rm.message = '只有镜片来片登记之后 的状态时才可以初检; 该订单当前状态为:{%s}' % lbo.get_status_display()
                    return rm

                obj = preliminary_checking()
                obj.laborder_id = lbo.id
                obj.lab_number = lbo.lab_number
                obj.laborder_entity = lbo
                obj.user_id = request.user.id
                obj.user_name = request.user.username
                obj.is_qualified = qualified
                obj.reason_code = reason_code
                obj.reason = reason
                obj.save()

                if qualified == True:
                    logging.debug('')
                    lc = lens_collection()
                    lc.pc_entity = obj
                    lc.laborder_entity = lbo
                    lc.laborder_id = lbo.id
                    lc.lab_number = lbo.lab_number
                    lc.user_id = request.user.id
                    lc.user_name = request.user.username
                    lc.save()

                    if not act_lens_sku == '':
                        if not lbo.act_lens_sku == act_lens_sku:
                            lbo.act_lens_sku = act_lens_sku
                            lbo.act_lens_name = act_lens_name

                    self.update_status(lbo.id)
                    # lbo.status = 'LENS_RECEIVE'
                    # lbo.save()
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'LENS_RECEIVE')
                    lbo.status = 'LENS_RECEIVE'
                    lbo.save()

                    # from django.db import connection
                    # cursor = connection.cursor()
                    # # 更新操作
                    # cursor.execute(
                    #     "update oms_laborder set status='LENS_RECEIVE' where lab_number='%s'" % lbo.lab_number)

                    logging.debug('1.----%s' % qualified)
                else:
                    lc = lens_return()
                    lc.pc_entity = obj
                    lc.laborder_entity = lbo
                    lc.laborder_id = lbo.id
                    lc.lab_number = lbo.lab_number
                    lc.user_id = request.user.id
                    lc.user_name = request.user.username
                    lc.reason_code = reason_code
                    lc.reason = reason
                    lc.save()

                    lbo.status = 'LENS_RETURN'

                    lbo.save()
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'LENS_RETURN', '镜片退货', reason)
                    logging.debug('2.----%s' % qualified)

                rm.obj = obj
                rm.code = 0
                rm.message = '此操作已成功'

            else:
                rm.code = -4
                rm.message = '订单未找到'
                return rm

        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)

        return rm

    def update_status(self, id, status='LENS_RECEIVE'):
        from django.db import connections, transaction
        with connections['default'].cursor() as c:
            try:
                with transaction.atomic(using='default'):
                    sql = "update oms_laborder set status='%s' where id=%s" % (status, id)
                    c.execute(sql)

            except Exception as e:
                return -2
        return 0


# 镜片收货
class lens_collection(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OLCT', editable=False)
    pc_entity = models.ForeignKey(preliminary_checking, models.SET_NULL,
                                  blank=True,
                                  null=True, editable=False)


# 镜片退货登记
class lens_return(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OLRE', editable=False)

    reason_code = models.CharField(u'原因代码', max_length=20, default='-1', null=True, blank=True)

    reason = models.CharField(u'原因', max_length=512, default='-1', null=True, blank=True)
    pc_entity = models.ForeignKey(preliminary_checking, models.SET_NULL,
                                  blank=True,
                                  null=True, editable=False)


# 成镜终检
class glasses_final_inspection(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OGFI', editable=False)

    prescripiton_actual_entity = models.ForeignKey(prescripiton_actual, models.SET_NULL,
                                                   blank=True,
                                                   null=True, editable=False)

    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)

    is_qualified = models.BooleanField(u'Is Quanlified', default=False)


# 成镜终检 - 技术数据
class glasses_final_inspection_technique(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='GFIT', editable=False)

    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)

    pd = models.DecimalField(u'pd', max_digits=5, decimal_places=1, default=0, null=True, blank=True)
    is_singgle_pd = models.BooleanField(u'single pd', default=True)
    od_pd = models.DecimalField(u'pd(OD)', max_digits=5, decimal_places=1, default=0, null=True, blank=True)
    os_pd = models.DecimalField(u'pd(OS)', max_digits=5, decimal_places=1, default=0, null=True, blank=True)

    od_prism = models.DecimalField(u'棱镜(OD)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    od_base = models.DecimalField(u'方向(OD)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    os_prism = models.DecimalField(u'棱镜(OS)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    os_base = models.DecimalField(u'方向(OS)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)

    od_prism1 = models.DecimalField(u'棱镜2(OD)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    od_base1 = models.DecimalField(u'方向2(OD)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    os_prism1 = models.DecimalField(u'棱镜2(OS)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)
    os_base1 = models.DecimalField(u'方向2(OS)', max_digits=5, decimal_places=2, default=0, null=True, blank=True)

    blue_blocker = models.BooleanField(u'Blue Blocker', default=False)
    polarized = models.BooleanField(u'polarized', default=False, )
    light_responsive = models.BooleanField(u'light responsive', default=False, )
    light_responsive_color = models.CharField(u'light responsive color', max_length=40, null=True, blank=True,
                                              default='',
                                              choices=choices_models.LENS_COLOR_CHOICES)
    co = models.BooleanField(u'CO', default=False, )
    tint = models.BooleanField(u'Tint', default=False, )
    tint_deepness = models.DecimalField(u'Tint Deepness', max_digits=5, decimal_places=0, default=0, null=True,
                                        blank=True)
    is_gradient = models.BooleanField(u'Gradient', default=False, )

    asmbl_seght = models.IntegerField(u'ASMBL SEGHT', default=0, null=True, blank=True, )
    od_asmbl_seght = models.IntegerField(u'OD ASMBL SEGHT', default=0, null=True, blank=True, )
    os_asmbl_seght = models.IntegerField(u'OS ASMBL SEGHT', default=0, null=True, blank=True, )

    is_d_thin = models.BooleanField(u'D-Thin', default=False, )

    is_qualified = models.BooleanField(u'Is Quanlified', default=False)

    assembler_id = models.IntegerField(u'Assembler ID', default=0, null=True, blank=True)
    # add lee 2020.8.4
    cutting_edge_user_id=models.IntegerField(u'Cutting Edge ID', default=0, null=True, blank=True)
    beauty_user_id=models.IntegerField(u'Beauty ID', default=0, null=True, blank=True)
    # end

    od_sub_mirrors_height = models.IntegerField(u'OD SUB MIRRORS HEIGHT', default=0, null=True, blank=True, )
    os_sub_mirrors_height = models.IntegerField(u'OS SUB MIRRORS HEIGHT', default=0, null=True, blank=True, )
    is_special_handling = models.BooleanField(u'Is SPECIAL HANDLING', default=False)
    od_tint_deepness = models.DecimalField(u'OD Tint Deepness', max_digits=5, decimal_places=0, default=0, null=True,
                                           blank=True)
    os_tint_deepness = models.DecimalField(u'OS Tint Deepness', max_digits=5, decimal_places=0, default=0, null=True,
                                           blank=True)
    clipon_qty = models.IntegerField(u'Clipon', default=0)
    is_polishing = models.BooleanField(u'Is Polishing', default=False)
    is_near_light = models.BooleanField(u'Is Near Light', default=False)
    coatings = models.CharField(u'膜层', max_length=32, default='HMC')
    npd = models.DecimalField(u'npd', max_digits=5, decimal_places=1, default=0, null=True, blank=True)
    od_npd = models.DecimalField(u'npd(OD)', max_digits=5, decimal_places=1, default=0, null=True, blank=True)
    os_npd = models.DecimalField(u'npd(OS)', max_digits=5, decimal_places=1, default=0, null=True, blank=True)


# 成镜终检 - 外观检查
class glasses_final_inspection_visual(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='GFIV', editable=False)

    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)

    is_qualified = models.BooleanField(u'Is Quanlified', default=False)


# 成镜终检错误记录
class glasses_final_inspection_log(qc_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='GFIL', editable=False)

    prescripiton_actual_entity = models.ForeignKey(prescripiton_actual, models.SET_NULL,
                                                   blank=True,
                                                   null=True, editable=False)
    reason_code = models.CharField(u'原因代码', max_length=20, default='-1', null=True, blank=True)

    reason = models.CharField(u'原因', max_length=512, default='-1', null=True, blank=True)


class glasses_final_inspection_controller:
    def add(self, request, json_obj):
        res = {}
        res['code'] = 0
        res['message'] = ''
        try:
            with transaction.atomic():
                # jgfi = json.loads(json_obj)
                lab_number = json_obj.get('lab_number')
                last_code = json_obj.get('last_code')
                last_error = json_obj.get('last_error')

                gfis = glasses_final_inspection.objects.filter(lab_number=lab_number)
                if len(gfis) > 0:
                    gfi = gfis[0]
                else:
                    gfi = glasses_final_inspection()

                gfi.lab_number = lab_number

                lbo = LabOrder.objects.get(lab_number=lab_number)

                # 有错误，记录错误，同时更新质检报告
                if not int(last_code) == 0:
                    gfil = glasses_final_inspection_log()
                    gfil.lab_number = lab_number
                    gfil.laborder_id = lbo.id
                    gfil.laborder_entity = lbo
                    gfil.reason_code = last_code
                    gfil.reason = last_error
                    gfil.save()

                    if lbo.status == 'GLASSES_RECEIVE' or lbo.status == 'FINAL_INSPECTION':
                        lbo.status = 'FINAL_INSPECTION_NO'
                        lbo.save()
                        tloc = tracking_lab_order_controller()
                        tloc.tracking(lbo, None, 'FINAL_INSPECTION_NO')
                    else:
                        res['code'] = -2
                        res['message'] = "只有【成镜收货】或【终检合格】状态的订单可以更新为【终检不合格】状态!请检查输入法状态和订单号！"
                        res['request_body'] = json_obj
                        return json.dumps(res)
                else:
                    # 只有成镜收货和终检不合格状态的订单 才能更改为终检
                    if lbo.status == 'GLASSES_RECEIVE' or lbo.status == 'FINAL_INSPECTION_NO':
                        lbo.status = 'FINAL_INSPECTION'
                        lbo.save()
                        tloc = tracking_lab_order_controller()
                        tloc.tracking(lbo, None, 'FINAL_INSPECTION')
                        gfi.is_qualified = True
                    else:
                        res['code'] = -2
                        res['message'] = "只有【成镜收货】或【终检不合格】状态的订单可以更新为【终检】状态!请检查输入法状态和订单号！"
                        res['request_body'] = json_obj
                        return json.dumps(res)

                pa = prescripiton_actual(**json_obj.get('prescription_actual'))
                pa.save()

                gfi.prescripiton_actual_entity = pa
                gfi.laborder_id = lbo.id
                gfi.laborder_entity = lbo

                gfi.save()
                res['message'] = 'Success'
                res['request_body'] = json_obj
                return json.dumps(res)

        except Exception as e:
            res['code'] = -1
            res['message'] = str(e)
            res['request_body'] = json_obj
            return json.dumps(res)


from oms.models.glasses_models import documents_base


class glasses_return(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='REVG', editable=False)

    LENS_RETURN_CHOICES = (
        ('-1', '未指定'),
        ('0', '整副'),
        ('1', '右片'),
        ('2', '左片'),

    )

    REASON_CHOICES = (
        ('-1', '未指定'),
        ('1', '镜片爆边'),
        ('2', '轴位不良'),
        ('3', '屈光度不良'),
        ('4', 'ADD不良'),
        ('5', '打孔裂片'),
        ('6', '开槽裂边'),
        ('7', '磨边不良'),
        ('8', '镜片划伤'),
        ('9', '镜架损坏'),
        ('10', '棱镜不良'),
        ('11', '瞳高不良'),
        ('12', '瞳距不良'),
        ('13', '镜片功能性不良'),
        ('999', '其他'),
    )
    RETURN_TYPE_CHOICES = (
        ('1', '镜片'),
        ('2', '镜架'),
    )
    lens_return = models.CharField(u'退片', max_length=20, default='-1', null=True, blank=True,
                                   choices=LENS_RETURN_CHOICES)
    lens_return_qty = models.IntegerField(u'退片数量', default=0)

    reason_code = models.CharField(u'原因代码', max_length=20, default='-1', null=True, blank=True)
    reason = models.CharField(u'原因', max_length=512, default='-1', null=True, blank=True)
    is_qualified = models.BooleanField(u'IS Qualified', default=False)
    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)
    idei_frame = models.CharField(u'镜架报损出库关联id', max_length=20, default='', null=True, blank=True)
    idei_lens_r = models.CharField(u'镜片_右报损出库关联id', max_length=20, default='', null=True, blank=True)
    idei_lens_l = models.CharField(u'镜片_左报损出库关联id', max_length=20, default='', null=True, blank=True)
    doc_type = models.CharField(u'返工类型', max_length=20, default='1', null=True, blank=True,
                                   choices=RETURN_TYPE_CHOICES)
    assembler_id = models.CharField(u'装配师 ID', max_length=20, default='')
    assembler_user_code = models.CharField(u'类型', max_length=20, default='')
    assembler_user_name = models.CharField(u'类型', max_length=20, default='')


class glasses_return_control:
    def add(self, request, data_dict):
        rm = response_message()
        rm.code = -9
        rm.message = '准备操作'
        try:
            logging.debug('开始进入 ...')
            logging.debug('没有重复记录')
            with transaction.atomic():
                loc = lab_order_controller()
                lbos = loc.get_by_entity(data_dict.get('lab_number'))

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]

                if not lbo == None:
                    objs = glasses_return.objects.all().order_by('-id')[:1]
                    # 2019.03.30 by guof.
                    # 去掉针对连续重复生成同一订单号的成镜返工单的限制
                    # 调整针对连续重复操作的限制规则
                    if len(objs) > 0:
                        ob = objs[0]
                        if ob.lab_number == lbo.lab_number \
                                and lbo.status == 'GLASSES_RETURN':
                            rm.code = -3
                            rm.message = '疑似重复操作'
                            return rm

                    if not lbo.status == 'FINAL_INSPECTION_NO' and \
                            not lbo.status == 'GLASSES_RECEIVE' and \
                            not lbo.status == 'FINAL_INSPECTION_YES' and \
                            not lbo.status == 'FINAL_INSPECTION':
                        rm.code = -4
                        rm.message = '只有 待装配/装配完成/终检/终检合格或终检不合格 的状态时才可以生成镜片返工; \n该订单当前状态为:{%s}' % lbo.get_status_display()
                        return rm

                    if data_dict.get('lens_check') == 'true':
                        lenreason = LensReason.objects.get(reason_code=data_dict.get('reason_code'))
                        obj = glasses_return()
                        obj.laborder_id = lbo.id
                        obj.lab_number = lbo.lab_number
                        obj.laborder_entity = lbo
                        obj.user_id = request.user.id
                        obj.user_name = request.user.username
                        obj.doc_type = '1'
                        obj.assembler_id = data_dict.get('assembler')
                        obj.assembler_user_code = data_dict.get('assembler_user_code')
                        obj.assembler_user_name = data_dict.get('assembler_user_name')
                        obj.reason_code = data_dict.get('reason_code')
                        obj.reason = lenreason.reason_name
                        obj.lens_return = data_dict.get('lens_return')
                        if obj.lens_return == '0':
                            obj.lens_return_qty = 2
                        else:
                            obj.lens_return_qty = 1
                        obj.comments = data_dict.get('comments')
                        obj.save()
                    if data_dict.get('frame_check') == 'true':
                        framereason = FrameReason.objects.get(reason_code=data_dict.get('frame_reason'))
                        obj = glasses_return()
                        obj.laborder_id = lbo.id
                        obj.lab_number = lbo.lab_number
                        obj.laborder_entity = lbo
                        obj.user_id = request.user.id
                        obj.user_name = request.user.username
                        obj.doc_type = '2'
                        obj.assembler_id = data_dict.get('assembler')
                        obj.assembler_user_code = data_dict.get('assembler_user_code')
                        obj.assembler_user_name = data_dict.get('assembler_user_name')
                        obj.reason_code = data_dict.get('frame_reason')
                        obj.reason = framereason.reason_name
                        obj.lens_return = ''
                        obj.lens_return_qty = 0
                        obj.comments = data_dict.get('frame_comments')
                        obj.save()
                    lbo.status = 'GLASSES_RETURN'
                    lbo.is_glasses_return = True
                    lbo.save()
                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, 'GLASSES_RETURN', '成镜返工', obj.reason)

                    rm.obj = obj
                    rm.code = 0
                    rm.message = '此操作已成功'

                else:
                    rm.code = -4
                    rm.message = '订单未找到'
                    return rm

        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)

        return rm



# 存储lab_order对应的video数据
class laborder_accessories(base_type):
    ANNEX_TYPE_CHOICES = (
        ('0', '未指定'),
        ('1', '图片'),
        ('2', '视频'),
        ('3', '其它'),
    )
    type = models.CharField(u'类型', max_length=20, default='LABA')
    laborder_entity_id = models.CharField(u'Laborder Entity', max_length=128, default='', blank=True, null=True,
                                          unique=False)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', blank=True, null=True, unique=False)
    tag = models.CharField(u'Tag', max_length=256, default='', blank=True, null=True, unique=False)
    key = models.CharField(u'Key', max_length=256, default='', blank=True, null=True, unique=False)
    base_url = models.CharField(u'Base Url', max_length=1024, default='', blank=True, null=True, unique=False)
    object_url = models.CharField(u'Object Url', max_length=128, default='', blank=True, null=True, unique=False)
    accessories_type = models.CharField(u'Annex Type', max_length=20, default='0', blank=True, null=True,
                                        choices=ANNEX_TYPE_CHOICES)
    qc_created_at = models.CharField(u'QC Created At', max_length=128, default='', blank=True, null=True, unique=False)
    qc_updated_at = models.CharField(u'QC Updated At', max_length=128, default='', blank=True, null=True, unique=False)


class laborder_accessories_controller:
    def add(self, request):

        res = {}
        data_list = json.loads(request.body)
        try:
            new_lv = laborder_accessories()
            new_lv.user_id = data_list['user_id']
            new_lv.user_name = data_list['user_name']
            new_lv.comments = data_list['comments']
            new_lv.laborder_entity_id = data_list['laborder_entity_id']
            new_lv.lab_number = data_list['lab_number']
            new_lv.tag = data_list['tag']
            new_lv.key = data_list['key']
            new_lv.base_url = data_list['base_url']
            new_lv.object_url = data_list['object_url']
            new_lv.accessories_type = data_list['accessories_type']
            new_lv.qc_created_at = data_list['qc_created_at']
            new_lv.qc_updated_at = data_list['qc_updated_at']
            new_lv.save()

            res['code'] = 0
            res['message'] = 'Success'
            json_res = json.dumps(res)
            return json_res
        except Exception as e:
            res['code'] = 0
            res['message'] = str(e)
            json_res = json.dumps(res)
            return json_res


class glasses_final_appearance_visual(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='GFAV', editable=False)
    is_frame = models.BooleanField(u'Is Frame', default=False)
    is_parts = models.BooleanField(u'Is Parts', default=False)
    is_lens = models.BooleanField(u'Is Lens', default=False)
    is_assembling = models.BooleanField(u'Is Assembling', default=False)
    is_plastic = models.BooleanField(u'Is Plastic', default=False)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)


class glasses_unqualified_items(base_type):
    item_id = models.IntegerField(u'Item Id', default=0)
    item_name = models.CharField(u'Item Name', max_length=128, null=True, blank=True, default='')
    appearance_id = models.IntegerField(u'Assembling Id', default=0)


class glasses_unqualified_items_config(base_type):
    TYPE_CHOICES = (
        ('FRAME', '镜架'),
        ('PARTS', '配件'),
        ('LENS', '镜片'),
        ('ASSEMBLING', '装配'),
        ('PLASTIC', '整形'),
    )
    item_name = models.CharField(u'Item Name', max_length=128, null=True, blank=True, default='')
    item_type = models.CharField(u'状态', max_length=128, null=True, blank=True, default='', choices=TYPE_CHOICES)


class LensReason(models.Model):
    class Meta:
        db_table = 'qc_lens_reason'

    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason_code = models.CharField(u'Reason Code', max_length=128, default='', blank=True, null=True)
    reason_name = models.CharField(u'Reason Name', max_length=128, default='', blank=True, null=True)


class FrameReason(models.Model):
    class Meta:
        db_table = 'qc_frame_reason'

    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason_code = models.CharField(u'Reason Code', max_length=128, default='', blank=True, null=True)
    reason_name = models.CharField(u'Reason Name', max_length=128, default='', blank=True, null=True)


class PreliminaryPrescripitonActual(prescripiton_base):
    class Meta:
        db_table = 'qc_preliminary_prescripiton_actual'
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='BAPA', editable=False)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)