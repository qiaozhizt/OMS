# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
#from urllib.parse import urlparse
from urlparse import urlparse
import json
import logging
import time,datetime
from bs4 import BeautifulSoup
from util.response import json_response

def read_ups_by_track_numbers(track_numbers):
    api_url = "https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1="
    qtc_tLabels1 = track_numbers
    api_url = api_url + qtc_tLabels1
    u = urlparse(api_url)
    ss = requests.session()
    form_data=[]
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Host": u.netloc,
        "Origin": ("http" if u.scheme == "" else u.scheme) + "://"+u.netloc,
        "Referer": "https://www.ups.com/",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
    }
    data = {
        "Locale": "zh_CN",
        "TrackingNumber": track_numbers
    }
    datastr = json.dumps(data)
    r = ss.post(api_url, headers=headers, data=datastr, timeout=10, verify=False)
    html_doc = r.text
    soup = BeautifulSoup(html_doc, 'html.parser', from_encoding='utf-8')
    if soup.select('.text_explanation')!='' and len(soup.select('.text_explanation'))>0:
        logging.debug(soup.select('.text_explanation'))
        status = soup.select('.text_explanation')[0].text
        delivery_date = soup.select('.status_feed')[0].find_all('p')[0].text
        delivery_date = delivery_date.strip()
        delivery_date = delivery_date.split('at')
        delivery_year = ''
        delivery_hour = ''
        if delivery_date != '' and len(delivery_date) >= 2:
            delivery_year = delivery_date[0].rstrip()
            delivery_hour = delivery_date[1].lstrip()
        form_data.append(delivery_year)
        form_data.append(delivery_hour)
        form_data.append(status)
    return form_data

def get_ship2_tracking_number(lab_number):
    data = {}
    try:
        api_url = "http://ship2.zhijingoptical.com/api/get_shipment_historuy/?lab_number="
        qtc_tLabels1 = lab_number
        api_url = api_url + qtc_tLabels1
        u = urlparse(api_url)
        ss = requests.session()
        ep_tracking_code=''
        ep_created_at =''
        ship_data = []
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Host": u.netloc,
            "Origin": ("http" if u.scheme == "" else u.scheme) + "://"+u.netloc,
            "Referer": "https://www.ups.com/",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
        }
        data = {
            "Locale": "zh_CN"
        }
        datastr = json.dumps(data)
        req = ss.get(api_url, headers=headers, data=datastr, timeout=10, verify=False)
        resp = req.text
        res_json = json.loads(resp)
        # logging.debug(res_json)
        if res_json["code"]==200:
            trackDetails = res_json["data"]["sh"]
            ep_tracking_code = trackDetails.get('ep_tracking_code', '')
            ep_created_at = trackDetails.get('ep_created_at', '')
            ep_label_url = trackDetails.get('ep_label_url', '')

            logging.debug('ep_tracking_code: %s' % ep_tracking_code)
            logging.debug('ep_created_at: %s' % ep_created_at)
            logging.debug('ep_label_url: %s' % ep_label_url)
            print(ep_created_at)
            # if ep_created_at!='':
            #     UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
            #     ep_created_at= datetime.datetime.strptime(ep_created_at, UTC_FORMAT)
            logging.debug(ep_created_at)
            ship_data.append(ep_created_at)
            ship_data.append(ep_tracking_code)
            ship_data.append(ep_label_url)
            data['code'] = 0
            data['msg'] = 'Success'
            data['ship_data'] = ship_data
            return data
        else:
            data['code'] = -1
            data['msg'] = 'Fail'
            data['ship_data'] = []
            return data
    except Exception as e:
        data['code'] = -1
        data['msg'] = e
        data['ship_data'] = []
        return json_response(code=-1, msg=e)


