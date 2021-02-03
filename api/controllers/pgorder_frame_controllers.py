# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from util.response import response_message

# Create your models here.

class pgorder_frame_controller:

    def get_lab_frame(self, data_dict):
        rm = response_message()
        try:
            rvalue = {}
            pg_frame = data_dict.get('pg_frame', '')
            category_id = pg_frame[0]
            lens_color = pg_frame[-1]
            if lens_color not in ['G', 'B', 'E']:
                lens_color = ''
                lab_frame = pg_frame[1:]
                sg_flag = False
            else:
                lab_frame = pg_frame[1:-1]
                sg_flag = True
            rvalue['category_id'] = category_id
            rvalue['lab_frame'] = lab_frame
            rvalue['sg_flag'] = sg_flag
            rvalue['lens_color'] = lens_color
            rm.obj = rvalue
            return rm
        except Exception as ex:
            rm.capture_execption(ex)
            return rm
