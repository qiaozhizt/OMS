# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import logging

from util.response import response_message
from models import *
from util.db_helper import *
from util.dict_helper import *
from util.response import *
from util.format_helper import *

from oms.models.order_models import LabOrder


class job_contoller:
    start_day = datetime.datetime.strptime('2019-04-01 00:00:01', '%Y-%m-%d %H:%M:%S')

    def get_all(self, parameters):
        rm = response_message()
        try:
            logging.debug('########################################')
            try:
                lenss = None
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

    def tracking(self, parameters):
        rm = response_message()
        logging.debug('job tracking ....')
        try:
            lbo = parameters.get('lbo', None)

            if lbo:
                status = lbo.status

                if not status:
                    status = 'NEW'

                last_status = None

                jts = job_tracking.objects.filter(entity_id=lbo.id).order_by('-id')
                jt = None

                if jts.count() > 0:
                    jt = jts[0]

                if jt:
                    last_status = jt.status

                if not last_status == status:
                    jt = job_tracking()
                    jt.status = status
                    jt.order_number = lbo.order_number
                    jt.entity_id = lbo.id
                    jt.lab_number = lbo.lab_number
                    jt.frame = lbo.frame
                    jt.lens_sku = lbo.lens_sku
                    jt.comments = lbo.comments

                    jt.save()
                    logging.critical('tracking ok ....')
                else:
                    logging.critical('repeat records ....')

            rm.obj = lbo
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
        return rm

    def archived(self, parameters):
        rm = response_message()
        logging.debug('job archived ....')
        try:
            lbo = parameters.get('lbo', None)

            if lbo:
                jts = job_archived.objects.filter(entity_id=lbo.id).order_by('-id')

                if jts.count() > 0:
                    jt = jts[0]
                    logging.critical('repeat records ....')
                else:
                    jt = job_archived()
                    jt.status = lbo.status
                    jt.order_number = lbo.order_number
                    jt.entity_id = lbo.id
                    jt.lab_number = lbo.lab_number
                    jt.frame = lbo.frame
                    jt.lens_sku = lbo.lens_sku
                    jt.comments = lbo.comments

                    jt.save()
                    logging.critical('archived ok ....')

            rm.obj = lbo
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
        return rm

    def get_last_entity_id(self, parameters):
        rm = response_message()
        try:
            objs = job_log.objects.all().order_by('-id')[:1]

            if objs.count() > 0:
                obj = objs[0]
                rm.obj = obj.last_entity_id
            else:
                rm.obj = 0

            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
        return rm

    def set_last_entity(self, parameters):
        rm = response_message()
        try:
            jl = job_log()
            last_entity_id = parameters.get('last_entity', 0)

            jl.last_entity_id = last_entity_id
            jl.save()

            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.debug(str(e))
        return rm
