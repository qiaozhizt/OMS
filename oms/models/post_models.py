# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json


class Prescription:
    '''
     Prescription Structure
     仅应用与数据传递，并无实体持久化
    '''

    def __init__( \
            self,
            id=0,
            prescription_type='S',
            active='1',
            rsph=0.00,
            lsph=0.00,
            rcyl=0.00,
            lcyl=0.00,
            rax=0,
            lax=0,
            rpri=0.00,
            lpri=0.00,
            rbase=0.00,
            lbase=0.00,

            rpri1 = 0.00,
            rbase1 = 0.00,
            lpri1 = 0.00,
            lbase1 = 0.00,

            radd=0.00,
            ladd=0.00,
            pd=0,
            single_pd=0,
            rpd=0.0,
            lpd=0.0,
            exam_date='',
            expire_date='',
            prescription_name='Defalut Rx',
            used_for='',
            is_prism=0,  # 是否包含棱镜
            sv_type='SS',  # Single vision Type 单光类型
            #     Shortsighted 近视[SS] 默认设置
            #     presbyopic 老花[PB]
            #     平光[N]
            # is_dff=0,  # 是否使用车房片，默认 False
            is_need_rx_lab=0
    ):
        self.name = 'prescription'
        self.id = id
        self.prescription_type = prescription_type
        self.active = active
        self.rsph = rsph
        self.lsph = lsph
        self.rcyl = rcyl
        self.lcyl = lcyl
        self.rax = rax
        self.lax = lax
        self.rpri = rpri
        self.lpri = lpri
        self.rbase = rbase
        self.lbase = lbase

        self.rpri1 = rpri1
        self.lpri1 = lpri1
        self.rbase1 = rbase1
        self.lbase1 = lbase1

        self.radd = radd
        self.ladd = ladd
        self.pd = pd
        self.single_pd = single_pd
        self.rpd = rpd
        self.lpd = lpd
        self.exam_date = exam_date
        self.expire_date = expire_date
        self.prescription_name = prescription_name
        self.used_for = used_for
        self.use_for = used_for  # 为了 mg site 上的问题，被迫使用错误代码
        self.is_prism = is_prism
        self.sv_type = sv_type

        self.is_need_rx_lab = is_need_rx_lab


class PushBox:

    def getJson(self, Carrier, PostMethod, OrderNumber, Remark, Pglist, Lalist, qty_inbox_list):
        self.Carrier = Carrier
        self.PostMethod = PostMethod
        self.OrderNumber = OrderNumber
        self.Remark = Remark
        self.Pglist = Pglist
        self.Lalist = Lalist
        self.qty_inbox_list = qty_inbox_list
        return json.dumps(self.__dict__)
