#!/usr/bin/python
# coding:utf-8

import os

class LocalHandler(object):
    def upload_file(self, make_dir_day, file_data):
        data = {}
        try:
            if not os.path.exists(make_dir_day):
                os.makedirs(make_dir_day)
            upload_file_path = make_dir_day + '/' + file_data.name
            with open(upload_file_path, 'wb') as f:
                for chunk in file_data.chunks():
                    f.write(chunk)
            new_file_path = "media" + upload_file_path.split("media")[1]
            data['url'] = new_file_path
            data['code'] = 0
            data['msg'] = "上传成功"
            return data
        except Exception as e:
            data['url'] = ''
            data['code'] = -1
            data['msg'] = e
            return data
