# -*- coding: utf-8 -*-
#from util.upload_aws import S3Handler
#from util.upload_sftp import SFTPHandler
from util.upload_local import LocalHandler
from util.response import json_response


class UploadFile(object):
    def upload_file(self, file_path, file_data, upload_flag):
        try:
            if upload_flag == 'LOCAL':
                local_handler = LocalHandler()
                json_data = local_handler.upload_file(file_path, file_data)
            #暂时不启用
            #elif self.upload_flag == 'SFTP':
            #    sftp_handler = SFTPHandler()
            #    json_data = sftp_handler.upload_file(file_path, file_data)
            #elif self.upload_flag == 'S3':
            #    s3_handler = S3Handler()
            #    json_data = s3_handler.save(file_data.name, file_data)
            return json_data
        except Exception as e:
            return json_response(code=-1, msg=e)

