# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.utils import timezone

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.db.models import Q

from django.http import HttpRequest
from api.models import DingdingChat


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start send monitor ....')
        # 2019.10.19 by guof.
        # send dingding message to monitor chat
        nw = datetime.datetime.now().strftime("%m-%dT%H:%M:%S")
        ddc = DingdingChat()
        ddc.send_text_to_chat('chatc3e669fecb84223c8d56a5bb2459fc7c', '[%s] - [%s]' % ("Cron Server", nw))

        logging.critical('send monitor ended ....')
