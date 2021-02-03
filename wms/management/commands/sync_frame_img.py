# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.views import namedtuplefetchall
import logging
from django.db import connections
import codecs
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller
from pg_oms.settings import SSH_MEDIA_SERVER
import paramiko
import requests
import os


'''
同步镜架图片
'''


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info('start ....')
        try:
            BASE_IMG_URl = 'https://static.payneglasses.com/media/catalog/product'
            web_sku_image = {}

            with connections['default'].cursor() as cursor, connections['magentodb'].cursor() as magentodbcursor:
                sql = """SELECT sku FROM wms_product_frame where image=''"""
                web_sql = """SELECT sku,image FROM catalog_product_flat_1"""
                magentodbcursor.execute(web_sql)
                for item in namedtuplefetchall(magentodbcursor):
                    if len(item.sku) < 7:
                        continue
                    else:
                        poc = pgorder_frame_controller()
                        res_rm = poc.get_lab_frame({"pg_frame": item.sku})
                        if not web_sku_image.has_key(res_rm.obj['lab_frame']):
                            if item.image is not None:
                                web_sku_image[res_rm.obj['lab_frame']] = item.image

                logging.info(sql)
                cursor.execute(sql)
                for lab_item in namedtuplefetchall(cursor):
                    lab_image = web_sku_image.get(lab_item.sku, '')

                    if lab_image == '':
                        continue
                    else:
                        img_url = BASE_IMG_URl + lab_image
                        local_img_url = self.download_img(img_url, 'local_img')
                        if local_img_url != '':
                            flag = self.upload_img(local_img_url, lab_image)
                            if flag:
                                update_sql = """UPDATE wms_product_frame SET image=%s,thumbnail=%s WHERE sku=%s"""
                                cursor.execute(update_sql, (lab_image, lab_image, lab_item.sku))


            logging.info('end ....')
        except Exception as e:
            logging.exception(e.message)

        logging.critical('所有操作成功结束 ....')

    def download_img(self,img_url, name):
        try:
            response = requests.get(img_url)
            img = response.content
            img_src = SSH_MEDIA_SERVER.get('LOCAL_MEDIA_BASE') + name + ".jpg"
            with open(img_src, 'wb') as f:
                f.write(img)
            return img_src
        except Exception as ex:
            return ''

    def upload_img(self, local_img_url, lab_image):
        try:
            private_key = paramiko.RSAKey.from_private_key_file(SSH_MEDIA_SERVER.get('SECRET_KEY'))
            transport = paramiko.Transport((SSH_MEDIA_SERVER.get('BASE_IP'), SSH_MEDIA_SERVER.get('SSH_PORT', 22)))
            transport.connect(username=SSH_MEDIA_SERVER.get('USER_NAME'), pkey=private_key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            make_dir_file = SSH_MEDIA_SERVER.get('UPLOAD_MEDIA_BASE') + 'catalog/product'
            lab_url_last = lab_image.split("/")[-1]
            make_upload_url = make_dir_file + lab_image.split(lab_url_last)[0]
            upload_src = make_dir_file + lab_image
            try:
                sftp.stat(make_upload_url)
            except IOError:
                ssh = paramiko.SSHClient()  # 创建SSH对象
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机
                ssh.connect(hostname=SSH_MEDIA_SERVER.get('BASE_IP'), port=SSH_MEDIA_SERVER.get('SSH_PORT', 22), username=SSH_MEDIA_SERVER.get('USER_NAME'), pkey=private_key)  # 连接服务器
                mkdir_src = "mkdir -p " + make_upload_url
                ssh.exec_command(mkdir_src)  # 执行命令

            sftp.put(local_img_url, upload_src)

            try:
                sftp.stat(upload_src)
                transport.close()
                os.remove(local_img_url)
                return True
            except IOError:
                pass
        except Exception as ex:
            return False

