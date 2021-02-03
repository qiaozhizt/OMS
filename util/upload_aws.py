#!/usr/bin/python
# coding:utf-8

from boto3.session import Session
from pg_oms.settings import AWS_CONFIG



class S3Handler(object):
    """连接AWS,上传文件，及获取文件路径"""
    def __init__(self):
        self.aws_key = AWS_CONFIG.get('AWS_KEY', '')  # id
        self.aws_secret = AWS_CONFIG.get('AWS_SECRET', '')  # 秘钥
        self.bucket_name = AWS_CONFIG.get('BUCKET_NAME', '')  # 桶名
        self.region_name = AWS_CONFIG.get('REGION_NAME', '')   # 此处根据自己的 s3 地区位置改变
        self.session = Session(aws_access_key_id=self.aws_key,
                          aws_secret_access_key=self.aws_secret,
                          region_name=self.region_name)

        self.s3 = self.session.resource("s3")
        self.client = self.session.client("s3")

    def save(self, upload_key, data):
        """上传 data 二进制数据"""
        data = {}
        try:
            self.s3.Bucket(self.bucket_name).put_object(Key=upload_key, Body=data)
            down_url = self.client.generate_presigned_url('get_object',
                                                          Params={'Bucket': self.bucket_name, 'Key': upload_key},
                                                          ExpiresIn=3600)
            data['url'] = down_url
            data['code'] = 0
            data['msg'] = "上传成功"
            return data
        except Exception as e:
            data['url'] = ''
            data['code'] = -1
            data['msg'] = e
            return data


    def get_url(self, upload_key):
        """文件路径"""
        down_url = self.client.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': upload_key},
                                                 ExpiresIn=3600)
        return down_url