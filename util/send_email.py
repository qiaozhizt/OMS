# -*- coding: utf-8 -*-
import smtplib
import logging
import json
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from util.response import *
from pg_oms.settings import SEND_EMAIL_CONFIG
import email.utils
from email.mime.multipart import MIMEMultipart


class SendEmail:
    def send_email(self, to_address, subject, text):
        rm = response_message()
        logging.debug('开始')
        # 第三方 SMTP 服务
        mail_host = SEND_EMAIL_CONFIG.get('MAIL_HOST')# 设置服务器
        mail_port = SEND_EMAIL_CONFIG.get('MAIL_PORT')
        mail_user = SEND_EMAIL_CONFIG.get('MAIL_USER')# 设置用户名
        mail_pass = SEND_EMAIL_CONFIG.get('MAIL_PASS')# 设置口令
        sender = SEND_EMAIL_CONFIG.get('SENDER')# 设置发送方
        mail_from = formataddr(["payneglasses", "dr.payne@email.payneglasses.com"])
        receivers = []  # 接收邮件地址
        # 添加接收地址,内容，标题
        if to_address == '' or to_address is None:
            rm.code = -2
            rm.message = 'Email address error'
            return rm
        receivers.append(to_address)
        # receivers.append("rhycyj@163.com")
        # receivers.append("haifeng@jayceeinc.com")
        # receivers.append("2643530660@qq.com")

        message = MIMEText(text, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = mail_from
        #add by ranhy 10-5
        message['To'] = ",".join(receivers)
        try:
            smtp_obj = smtplib.SMTP(mail_host, mail_port)
            smtp_obj.ehlo()
            smtp_obj.starttls()
            smtp_obj.ehlo()
            logging.debug('邮件对象创建成功')
            smtp_obj.login(mail_user, mail_pass)
            logging.debug('连接成功')
            smtp_obj.sendmail(sender, receivers, message.as_string())
            smtp_obj.close()
            logging.debug('结束')
            rm.message = 'send success'
            return rm
        except Exception as e:
            logging.debug(str(e))
            rm.code = -1
            rm.capture_execption(e)
            return rm

    def send_html_email(self,to_address,subject):
        rm = response_message()
        logging.debug('开始')
        # 第三方 SMTP 服务
        mail_host = "smtp.exmail.qq.com"  # 设置服务器
        mail_user = "gaoyu@jayceeinc.com"  # 设置用户名
        mail_pass = "Swaqw2q1!"  # 设置口令
        sender = 'gaoyu@jayceeinc.com'  # 设置发送方
        receivers = []  # 接收邮件地址
        # 读取html文件内容
        f = open('dc/templates/email_form.html', 'r', encoding='utf-8')
        mail_body = f.read()
        f.close()
        # 添加接收地址,内容，标题
        if to_address == '' or to_address is None:
            rm.code = -2
            rm.message = 'Email address error'
            return rm
        receivers.append(to_address)
        message = MIMEText(mail_body, _subtype='html', _charset='utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = Header("Payne Glasses", 'utf-8')
        try:
            smtp_obj = smtplib.SMTP_SSL(mail_host, 465)
            logging.debug('邮件对象创建成功')
            smtp_obj.login(mail_user, mail_pass)
            logging.debug('连接成功')
            smtp_obj.sendmail(sender, receivers, message.as_string())
            smtp_obj.close()
            logging.debug('结束')
            rm.message = 'send success'
            return rm
        except Exception as e:
            logging.debug(str(e))
            rm.code = -1
            rm.capture_execption(e)
            return rm
