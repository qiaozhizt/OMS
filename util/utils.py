# -*- coding: utf-8 -*-
import datetime


class Utils:
    @staticmethod
    def array_segmentation(arr, size):
        s = []
        for i in range(0, int(len(arr)) + 1, size):
            c = arr[i:i + size]
            s.append(c)
        return s


class FileHelper:
    file_name = 'log.log'

    def __init__(self, file_name):
        self.file_name = file_name

    def write(self, msg):
        try:
            with open(self.file_name, 'a') as file_obj:
                file_obj.write(msg)
        except Exception as ex:
            with open(self.file_name, 'w') as file_obj:
                file_obj.write(msg)


class LogHelper:
    log_file_name = 'log.log'

    fh = None

    def __init__(self, file_name):
        self.log_file_name = file_name
        self.fh = FileHelper(self.log_file_name)

    def write(self, msg):
        now = datetime.datetime.now()
        msg = "%s %s%s" % (now, msg, '\n')
        self.fh.write(msg)
