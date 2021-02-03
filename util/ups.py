# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
#from urllib.parse import urlparse
from urlparse import urlparse
import json
import logging
import time,datetime
def read_ups_by_track_numbers(track_numbers):
    api_url = "https://www.ups.com/track/api/Track/GetStatus?loc=zh_CN"
    u = urlparse(api_url)
    ss = requests.session()
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
    return r

def read_ups_by_track_number(track_number):
    api_url = "https://www.ups.com/track/api/Track/GetStatus?loc=zh_CN"
    u = urlparse(api_url)
    ss = requests.session()
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
        "TrackingNumber": [track_number]
    }
    datastr = json.dumps(data)
    r = ss.post(api_url, headers=headers, data=datastr, timeout=10, verify=False)
    return r

def run(track_number):
    # track_number=["1ze8377x0471697257",]
    # r=read_ups_by_track_numbers(track_number)
    # d=json.loads(r.text)
    # trackDetails=d["trackDetails"]
    # for trackDetail in trackDetails:
    #     trackingNumber=trackDetail["trackingNumber"]
    #     leftAt = trackDetail["trackSummaryView"]["leftAt"]
    #     packageStatus = trackDetail["trackSummaryView"]["packageStatus"]
    #     packageStatusCode = trackDetail["trackSummaryView"]["packageStatusCode"]
    #     packageStatusDate = trackDetail["trackSummaryView"]["packageStatusDate"]
    #     packageStatusDateTimeLabel = trackDetail["trackSummaryView"]["packageStatusDateTimeLabel"]
    #     packageStatusDateWithYear = trackDetail["trackSummaryView"]["packageStatusDateWithYear"]
    #     packageStatusIconType = trackDetail["trackSummaryView"]["packageStatusIconType"]
    #     packageStatusTime = trackDetail["trackSummaryView"]["packageStatusTime"]
    #     print(trackingNumber,packageStatusCode,leftAt,packageStatus,packageStatusDate,packageStatusDateTimeLabel,packageStatusDateWithYear,packageStatusIconType,packageStatusTime)

    # r=read_ups_by_track_number("1ZW682790452495807")
    r = read_ups_by_track_number(track_number)
    d = json.loads(r.text)
    trackDetails = d["trackDetails"]
    form_date = ''
    shiping_date = ''
    data=[]
    if trackDetails[0]["shipmentProgressActivities"] !=None:
        for progress in trackDetails[0]["shipmentProgressActivities"]:
            date = progress["date"]
            time = progress["time"]
            location = progress["location"]
            activityScan = progress["activityScan"]
            actCode = progress["actCode"]  # 妥投可能是 FS
            logging.debug(actCode)
            actCode = str(actCode)
            actCode=actCode.rstrip()
            if actCode == 'FS' or actCode == 'KB' or actCode == '9E' or actCode == 'KE' or actCode == 'KM' \
                    or actCode=='2W':
                if actCode == 'FS':
                    activityScan=str(activityScan)
                    if activityScan.rstrip() == '已递送' or activityScan.rstrip() == 'Delivered':
                        form_date = date + " " + time
                        logging.debug(form_date)
                        data.append(form_date)
                else:
                    form_date = date + " " + time
                    logging.debug(form_date)
                    data.append(form_date)
            if actCode == 'MP':
                shiping_date = date + " " + time
                data.append(shiping_date)
            print(date, time, location, activityScan, actCode)
        logging.debug(data)
        return data
    else:
        return data

