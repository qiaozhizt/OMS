# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import logging
import json
import urllib2
import requests


# Create your models here.
class response_address:
    street1 = ""
    street2 = ""
    city = ""
    state = ""
    zip = ""
    country = "US"
    company = "EasyPost"
    phone = ""


class response_message:
    error_code = 0
    error_message = 'Success'
    obj = None


class DingdingChat:
    # default for 智镜
    appkey = 'dingl4ffi9i8c4zl2m41'
    appsecret = 'VZ7L2ue_Fasulcv40CfrmBdLmKLDAgwLWQPDEr1Fd3PlB2TM5caVVjIGpwbYlaRr'

    def send_message_plain_text(self, agent_id, text):
        access_token = self.get_access_token()
        return self.__send_convert_to_chat(access_token, agent_id, text)

    def send_text_to_chat(self, chat_id, text, mobile=None):
        access_token = self.get_access_token()
        msg_type, msg = self.__gen_text_msg(text)
        msg_dict = {
            "msgtype": msg_type
        }
        msg_dict[msg_type] = msg
        # logging.debug(msg_dict)
        # 是否需要@人,只有机器人接口存在此参数
        at_type, at_msg = self.__gen_at(mobile)
        msg_dict[at_type] = at_msg
        return self.__send_msg_to_chat(access_token, chat_id, msg_dict)

    def __send_convert_to_chat(self, access_token, agent_id, text):
        msg_type, msg = self.__gen_text_msg(text)
        msg_dict = {
            "msgtype": msg_type
        }
        msg_dict[msg_type] = msg
        logging.debug(msg_dict)
        return self.__send_corpconversation_to_chat(access_token, agent_id, msg_dict)

    def __gen_text_msg(self, text):
        msg_type = 'text'
        msg = {"content": text}
        return msg_type, msg

    def __gen_at(self, mobile):
        at_type = 'at'
        at_msg = {
            "isAtAll": 1
        }
        return at_type, at_msg

    def __send_msg_to_chat(self, access_token, chat_id, msg_dict):
        logging.debug(access_token)
        logging.debug(chat_id)
        # logging.debug(msg_dict)
        body_dict = {
            "chatid": chat_id
        }
        body_dict['msg'] = msg_dict
        body = json.dumps(body_dict)
        # logging.debug(body)
        return self.__send_msg("https://oapi.dingtalk.com/chat/send?access_token=" + access_token, access_token, body)

    def __send_corpconversation_to_chat(self, access_token, agent_id, msg_dict):
        logging.debug(access_token)
        logging.debug(agent_id)
        logging.debug(msg_dict)
        body_dict = {
            "agent_id": agent_id
        }
        body_dict['msg'] = msg_dict
        body = json.dumps(body_dict)
        logging.debug(body)
        return self.__send_msg(
            "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token=" + access_token,
            access_token, body)

    def get_access_token(self):
        url = 'https://oapi.dingtalk.com/gettoken?appkey=%s&appsecret=%s'
        url = url % (self.appkey, self.appsecret)
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        response_str = response.read()
        response_dict = json.loads(response_str)
        logging.debug(response_dict)
        error_code_key = "errcode"
        access_token_key = "access_token"
        if response_dict.has_key(error_code_key) and response_dict[error_code_key] == 0 and response_dict.has_key(
                access_token_key):
            return response_dict[access_token_key]
        else:
            return ''

    def __send_msg(self, url, access_token, body):

        rm = response_message()

        logging.debug("req_url==>%s" % url)

        http_headers = {
            'Content-Type': 'application/json',
            "Charset": "UTF-8"
        }

        logging.debug("http_headers==>%s" % http_headers)
        send_data = body
        send_data = json.loads(send_data)
        logging.debug(send_data)

        try:
            req = requests.post(url=url, json=send_data, headers=http_headers)
            resp = req.text
            logging.debug(resp)
            res_json = json.loads(resp)
            logging.debug('resp: %s' % resp)
            errcode = res_json.get('errcode', '')
            errmsg = res_json.get('errmsg', '')
            rm.code = errcode
            rm.message = errmsg

            return rm

        except Exception as e:
            logging.exception(str(e))
            rm.code = 1
            rm.message = str(e)
            return rm
