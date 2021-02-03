#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import base64
import hashlib
from oms import const

class AuthCode(object):

    @classmethod
    def encode(cls, string, key, expiry=0):
        """
        编码
        @param string: 带编码字符串
        @param key: 密钥
        @return:加密字符串
        """
        return cls._auth_code(string, 'ENCODE', key, expiry)

    @classmethod
    def decode(cls, string, key, expiry=0):
        """
        解码
        @param string: 待解码字符串
        @param key: 密钥
        @return:原始字符串
        """
        return cls._auth_code(string, 'DECODE', key, expiry)

    @staticmethod
    def _md5(source_string):
        return hashlib.md5(source_string).hexdigest()

    @classmethod
    def _auth_code(cls, input_string, operation='DECODE', key='', expiry=3600):
        """
        编码/解码
        @param input_string: 原文或者密文
        @param operation: 操作（加密或者解密，默认是解密）
        @param key: 密钥
        @param expiry: 密文有效期，单位是秒，0 表示永久有效
        @return: 处理后的原文或者经过 base64_encode 处理后的密文
        """

        # ----------------------- 获取随机密钥 -----------------------

        rand_key_length = 4
        # 随机密钥长度 取值 0-32
        # 可以令密文无任何规律，即便是原文和密钥完全相同，加密结果也会每次不同，增大破解难度
        # 值越大，密文变动规律越大，密文变化 = 16 的 ckey_length 次方，如果为 0，则不产生随机密钥

        key = cls._md5(key)
        key_a = cls._md5(key[:16])
        key_b = cls._md5(key[16:])
        if rand_key_length:
            if operation == 'DECODE':
                key_c = input_string[:rand_key_length]
            else:
                key_c = cls._md5(str(time.time()))[-rand_key_length:]
        else:
            key_c = ''

        crypt_key = key_a + cls._md5(key_a + key_c)

        if operation == 'DECODE':
            handled_string = base64.b64decode(input_string[rand_key_length:])
        else:
            expiration_time = expiry + int(time.time) if expiry else 0
            handled_string = '%010d' % expiration_time + cls._md5(input_string + key_b)[:16] + input_string

        rand_key = list()
        for i in xrange(256):
            rand_key.append(ord(crypt_key[i % len(crypt_key)]))

        # ----------------------------------------------------------

        box = range(256)
        j = 0
        for i in xrange(256):
            j = (j + box[i] + rand_key[i]) % 256
            tmp = box[i]
            box[i] = box[j]
            box[j] = tmp

        #for i in xrange(len(box)):
        #    print str(box[i]).rjust(5),
        #    if ((i + 1) % 10) == 0:
        #        print ''

        result = ''
        a = 0
        j = 0
        for i in xrange(len(handled_string)):
            a = (a + 1) % 256
            j = (j + box[a]) % 256
            tmp = box[a]
            box[a] = box[j]
            box[j] = tmp
            result += chr(ord(handled_string[i])^(box[(box[a]+box[j])%256]))

        if operation == 'DECODE':
            if (int(result[:10]) == 0 or (int(result[:10]) - time.time() > 0)) and \
                    (result[10:26] == cls._md5(result[26:] + key_b)[:16]):
                output_string = result[26:]
            else:
                output_string = ''
        else:
            output_string = key_c + base64.b64encode(result)

        return output_string

    @classmethod
    def decode_ex(self,data):
        data=str(base64.b64decode(data.encode("utf-8")),"utf-8")
        data=AuthCode.decode(data,const.AUTHCODE["secret_key"])
        return data

    @classmethod
    def encode_ex(cls,string):
        data = AuthCode.encode(string, const.AUTHCODE["secret_key"])
        b_str = base64.b64encode(data.encode())
        return b_str.decode()

    @classmethod
    def decode_base64(self,data):
        b_str = str(base64.b64decode(data.encode("utf-8")), "utf-8")
        return b_str

    @classmethod
    def encode_base64(self,data):
        b_str = base64.b64encode(data.encode())
        return b_str.decode()

if __name__ == '__main__':
    print(AuthCode.encode_ex(str(2208)))

    # src = 'My name is Hu Ang, I\'m a programmer.'
    # key = 'fr1e54b8t4n4m47'
    # encoded_string = AuthCode.encode(src, key)
    # decoded_string = AuthCode.decode(encoded_string, key)
    # print('Source String:', src)
    # print('After Encode :', encoded_string)
    # print('After Decode :', decoded_string)
    # print('----------------------------------------------')
    # # 通过 PHP 方式加密得到的一个密文，然后用 Python 解密
    # # $source_string = "My name is Hu Ang.";
    # # $secret_key = 'fr1e54b8t4n4m47';
    # # $encoded_string = authcode($source_string, 'ENCODE', $secret_key, 0);
    # php_encoded_string = '82798mEQ6ouQo1rFrbSXT5EHVjZ0gH0WuuZDXd9us/q44JAhmPwBAFZqvwXhvnjgUOJ+5aYh5ed8zNL3cjTOGBY='
    # print('Decode string encoded via php:', AuthCode.decode(php_encoded_string, key))
    # # PS：Python 方式加密过的字符串通过 PHP 解析也成功了。

    # s="OWEwNVVPR2dkVGJHeW5QVUsvSzh2dS9FY0ZLenpuS0lTa3djNmYyWXRob0RiTnpYampnZGh5emxSQmgzTzUvci9zbVF0eXI0b2NuOHQ2QmdPeElmQnRFTWV6RVkxaVozb2NsNSt6L3dJSzdLQnQ0dWlmMTRmeFJrQ3lVb1VscFdEaG90aEhrT2FFRS9ZRWNSZUk3ZG05d0t5YmNyc2xlK2lvNTU1N0R6RkhCY2lUQ1pQTWNMOHV0UmFFclExaVlCc3EwdVJ4a2NIdWdjdUhGdncvakFuWWh2ejhQZ3BrWncxazlnUXQvQjVOYWwycS9hTnhWK3NaTmJrR2RickZGQlE0YTk1dU05S1hmVEs0a2QzcnBXZC84YUJ2Q1BtSzNOQ1JISURvMEJpaEREVTUxaEJ3TTdCdXcrcy9lUklleXZiZ0cvck5Ba2hxL0dJcUE3cHh2MWxWMzFOVWU0RmdObUJkZnQ3UTl2aW5vRnFIU2cxU1JkRXZ5QjhLTmZBWjRwdDVjK2srV0RidnhRYmZmWWdyejVwdzlaL25STjJGMExjUytWaVF2R3NvR1lIenN4SzY3K0duNTNlbndJK1JZQ3hzRkNZRTlaenMrL1hvTllZV1R6a2I1TzZZaTQzUU9kVkVQMkxUMldFQm1LZisrUWkzd24zT1EybjBGeFR1djFDT2NwOXA3bDhMSExhLzl2K25MdnQvTXgxNDNYdkYyS3lMVE50SXNBZnZ1d0NkYVQ1N1hxMWlDRTFDUUNVbnljQ0xwQnN4SDdNeWZzY090VExmWkc3MndxeTVWbHh2b05Pc1ZhRDQzRUhiQ0VXQzM2L1VCeTR0TTBXZjRSREZsdkloMWY3M1ljcGpzbWYxYzYzQVFyNS9RcmlyY3Rkd2crSG83NTRvaEgyNTJjZnlNZXRWRFNSRWk1NmFnZ0U0WG9ZY1BaNkVldzVwUzFUNEFpVDZTdTZyUktXdzlCbVBaRHlkOFIzUnA5ZElEN0ZpRloxQ1ZPVHJmcXFOT2g5NlVSVlcySE9vVWZUT3FDRUM4Sk9JeTZIOE9CWkRqbTJSTS96YXpwM1N6L1dnTDUyUWsvUzdMWTMxSGZVYlZHZmZIZFMzZjlpTm12a295RXFhWjBrUWlnWDZ3NTFYSDRUQ2cvK2xmSEZ4L29pWUtpWk5FV0FZV0hSVzhrWXJPU0tGTllkVHhUeUp5enh0cjZicUhMc2crVU5vWlhlVkNxZThNM2g2SER2OXBtczVBK3pmZ01MUm9GbWxXcCtiSXBWZDFaTVFHSnZXMzUrVVBsK2VtRHF6cVBkSUE1QUl0UVRKVzBsb0tSQ1dla2F1TFZjSVZvbUVneksvaWx1SG1wRGNqaGRueU1QYzg5UTBBbXJpYWNPTUc3blhqSE50VFZNVWlsaHJ6alhaa2JjZ2wyaS80Q2NneEJSY3ZRTm1KYXFhVjNTaGJUMTFVR3RwUUJTejJCaFpxUnFjNTN3KzZFaThkOEtRZ0NpbFpVUmU3RDVJRUgwaWpwNjZ3THNvYThxNTFkRWNCUXdBd2Z3N3R1b254TVRFazgyVDBvaHJveTVIZ25hRjUxN2szY1hiMjRQS2VIMnA2N2dpS0dmaDBSaVpzNHp3YnJCYkpGd2RnWHhjNGFoNHVlRkE0THp6VDR5VTZmc0QvSW4ycURxNzlGOVpWTFhGMERzT2c1RHRVYVREQzQ4K1BXWllKNlMwSUhVSXNFSUt4emRMMG1mcC8xNnZBNDYveDJ5NEJYRmtLQUFidm1TREdMZ1k5QkdTV1J0TDdUclltQWUrY00vV3BydUxWdGZ1MmtBQUVuOXpmNUZ4Z1ZFTXJMSVcxMmZ6c1l5ci90TlQvOExMdGVva200MkVKZEhPRVpwZGlzVEF6cWFxVkswTGo3SW9HdnRwRkJJS2h6dS9tR3AxakluN3JGMkN2VVA0SmpTZFZDcFlmZnhpKy9mWkNSOENNY3M0QUNheG4wL3g5eU94KzhNM0ZGV0NmelpaUHhwRTM4TFFGTmtWeDRYcno2cDdnWkFwcDlSSXBDTktDWVI2QkFnNHdueUZoSU9sUTVldnZad21FNjdTek45clBvSTl0MmlCcDh6cURjQ0ZUZGJYZDFPMUdaaEI5WW1SdVNQSWFST3JxdmlLdHVzNzRJdWw3WFVNQnlOdGsxVnRaQnB1V2pnYlpVc3FhR0JBRWZVYXNEM2dCMkRKS3dtaE4yaEpNTUN5Uy9uMTUrZ3hJOW0vYXNpQ25CRjZyYU03bnluV215Yk4zbWtXcDYzZStpOUJsbXI3ZXgyUmpOWTZaRzdRNUQ5Q0liZnNxQng4Mm1Eb2FrdnAwTXVWY3hGc2JOZFNUWkNwYTZqWVExWEFkRWRKRm1Qd2RReDJER3U0YzZEKzhQU1BFUENaSDJ2ejBHNVVjVGllSjVjTU01NFVSVkk5YWJnTVM5ZkJVL21jSXVRYnRJbFVrTXJNdlJ2RzdaYkhDcm5HUkFkQXpsd2VxNUVJYSt5b3RCWTIxSlQ2NzZHSE8rZS8rVlZuYmJxZjdzUXV5YXFISk5jVFMrMjc4akNuemdjOGQwcDBQenpYMDlvSVF2RXNQL09GcHh1M2tjZW9HN3lyNUdIYmtCWHVCNUVSbTh0cEFjcjliNmZZOW5xUmdISzAyTUhyaUxrdFBaMXJRcjRiRjF1TmtuWElXamkxL1VwV1hXbjZ4TDNXMWs4TDlGbU84dVM5ZXRQbExLbEtFV1lqZVFoR0kzM2FIYkVJNnhKbFBxNUhrQmc3ekkvUlA5ME1xS2t6biszV1ZCUi8xWXY2K2hrMDdwdVpxaFRuTXAzZzNsVWc5RjNwbitOd0xzUXk5TEE3a0h1eHkrS0RDc291d1Y1b211bmloZXYzR0RKeTZMVFZhTXFoSGhTR0ZSZjFqV0ZTN2FmWVlNNlp1V1ZJWkRpMy9OTW5zSVYrMGNEZWJxemRYQ1RnV3VWSEc3aXlFV1c4blM0VTYwYW43S29BMWFaVHN4OHZ4Q2FsaTJyMUM2NjlMSjhOWFNNWHB3RkwzdUhJTjFPcmdBbVl2NlJheTU4YWEvSFVPWEJnV3BEdU8yRlFROGN4RkNGc2gyeFZDRmVtY2diZjFNemRtWUdaaFVxV2hSY0xVU1ZnL2lvRlgySW5CZURPUFh6YjJXKzFTbEJDbVFiOG8rVUZKYnBVaHFSM1RuaHRBSFUyWDRHc3cwSE1EemlQaitTUkl3eHJZQWl3LzhUQll3cjUrZkVYUGtONjlyYnh0dEVkYjNIYjZ0Rk5Ud3dsQWlxOFJqS3BMeGN2UzIvblBralZaMzIrVjQrMWZMd2tnTzYrTXJXbzZ6aXBzbnJGcGNScVJTOFZEdHJrc0drd2d3TkxrMkNvYTFCSVZNNm44TnZ5QmF6bDllZ0lpY01jRjMyekNyR3RoeXBsTVF5ck5kdUVOZDBnaERQcVJ5azhSV3ZCVm1CNnlTMnVRdTk5M1JLUHVnLzd3QWxDSzJDV2NEZ0lOdE90bnVXdnROM0dOK0ZDVENIemdOQWczRnRtMWJERnYwc2ZsUC80SHpSVDYrSVpxT05yTWhsVXdRMFRIeTFDZTdEOEVoOTl1TjJZVUxRZWl0cUgyU3Y5dDZrYTFKRW1MSEc3QWpOczdjUUdxdlhYaWt4WnhBNktPcTVvcGVEaitMb1h3cXhkNE1JQUhkUGRpODFreVBBM29qT1d5TDF3RjJzTVk0NGZrdXpBcWRab09EUHdlRG5NekpKS1J5aEV4aXhDcVNpbWx1YzR3ckUrbGJOTDc4UCttOFRweDJyb2V4Q215N1lNbzczYzhPSGtYaUJYVFhEUUVxTk00NHVQVnFpR25teWsrT2pYVGk0aG9Yc1M2RytGOTlBWG01Tlk5RFUwUDZPSk1VTFQ3SkNoL2ZLdGdsRUUxRDhpcTV1NHdzb1J2bFFaZFlHZzk4YTRMM3JQby9JY1NCQ05UTEo0ZnBXQldrRjlSSFVPTi9jaGZSTVE2MDh1L3JabnNIa2J5YnZiMmRpb2UzS2JCN3haTTB1cTNMTklJWTZWN3JJQkdMSXFUWFp5MGJ6YS9qTVB3R3h4UitTY2huOU9Icmw3RjQrMlE4bnhpVnhRQU9CeWZ6SjZndG9pT2phVkdVQzFyZFFjeFBpaTFzVmNaV3JsNHl3WlZMUjFTWFR6U2lIZW5jbk0yOXVxeU1weG9KdDU2bllPQnRHVm4zOTJHNTNHR0pENFk3VUVHbWdnVmpTTVQzWFJERnhnWE9KNnc0bStWOXpKa1JYOTFGdVpadmR1ZjJ2eW84b2ZqM01oYVhQYzNsSlM1TVIrY2cyazFjeEtwbkE1eUp6UDh3RlFpOE5Vd3hoMmVUNUlWSHlNL0tuRlVuK1IwMytub250ZnV3b09jYzF6N3Vpd3d1aTF6aGE5VXkwc1MxSzY2dGF1SnI3NW5Ya0FmL3BZZHFLV1U9"
    # s = base64.b64decode(s.encode("utf-8"))
    # s=str(s,"utf-8")
    # d=AuthCode.decode(s, ")(*&)(JOIJOIYO^(*&YUFGUFUTRE^FGVL908jk+{}{?:<:<K*Y&^*YU&(UOIMJ")
    # print(d)
