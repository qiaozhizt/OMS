#!/usr/bin/python
# coding:utf-8
import paramiko
from pg_oms.settings import VCA_MEDIA_SERVER


class SFTPHandler(object):
    def save_lacal_file(self, file_path, file_data):
        try:
            local_file_src = VCA_MEDIA_SERVER.get('LOCAL_MEDIA_BASE') + '\\' + file_data.name
            with open(local_file_src, 'wb') as f:
                for chunk in file_data.chunks():
                    f.write(chunk)
            return local_file_src
        except Exception as ex:
            return ''

    def upload_file(self, file_path, file_data):
        try:
            data = {}
            private_key = paramiko.RSAKey.from_private_key_file(VCA_MEDIA_SERVER.get('SECRET_KEY'))
            transport = paramiko.Transport((VCA_MEDIA_SERVER.get('BASE_IP'), VCA_MEDIA_SERVER.get('SSH_PORT', 22)))
            transport.connect(username=VCA_MEDIA_SERVER.get('USER_NAME'), pkey=private_key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            upload_file_path = file_path + '\\' + file_data.name
            local_file_src = self.save_lacal_file(file_path, file_data)
            try:
                sftp.stat(file_path)
            except IOError:
                ssh = paramiko.SSHClient()  # 创建SSH对象
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机
                ssh.connect(hostname=VCA_MEDIA_SERVER.get('BASE_IP'), port=VCA_MEDIA_SERVER.get('SSH_PORT', 22), username=VCA_MEDIA_SERVER.get('USER_NAME'), pkey=private_key)  # 连接服务器
                mkdir_src = "mkdir -p " + file_path
                ssh.exec_command(mkdir_src)  # 执行命令

            sftp.put(local_file_src, upload_file_path)

            try:
                sftp.stat(upload_file_path)
                transport.close()
                data['url'] = upload_file_path
                data['code'] = 0
                data['msg'] = "上传成功"
            except IOError:
                data['url'] = ''
                data['code'] = -1
                data['msg'] = "上传失败"
                return data
        except Exception as e:
            data['url'] = ''
            data['code'] = -1
            data['msg'] = e
            return data


