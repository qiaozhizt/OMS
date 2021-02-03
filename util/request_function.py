# -*- coding: utf-8 -*-
import datetime
import time
import simplejson as json
import decimal
from util.request_api import RequestApi


class RequestFunction():
    BASE_URL = ""

    def __init__(self):
        self.req_api = RequestApi()

    def get_laborders(self, params):
        pass
        # self.req_api.call_api(
        #     url=self.req_api.get_url(self.BASE_URL, '/ss', params),
        #     method="GET",
        #     params=params
        # )