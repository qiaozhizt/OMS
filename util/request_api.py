#! /usr/bin/env python
# coding=utf-8

import os
import re
import json
import time
import logging
import random
import hashlib

import datetime
import requests

_logger = logging.getLogger('api')

class ConnectionError(Exception):
    def __init__(self, response, content=None, message=None):
        self.response = response
        self.content = content
        self.message = message

    def __str__(self):
        message = u"Failed."
        if hasattr(self.response, 'status_code'):
            message += u" Response status: %s." % (self.response.status_code)
        if hasattr(self.response, 'reason'):
            message += u" Response message: %s." % (self.response.reason)
        if self.content is not None:
            message += u" Error message: " + self.content
        return message


class Redirection(ConnectionError):
    """3xx Redirection
    """

    def __str__(self):
        message = super(Redirection, self).__str__()
        if self.response.get('Location'):
            message = u"%s => %s" % (message, self.response.get('Location'))
        return message


class MissingParam(TypeError):
    pass


class MissingConfig(Exception):
    pass


class ClientError(ConnectionError):
    """4xx Client Error
    """
    pass


class BadRequest(ClientError):
    """400 Bad Request
    """
    pass


class UnauthorizedAccess(ClientError):
    """401 Unauthorized
    """
    pass


class ForbiddenAccess(ClientError):
    """403 Forbidden
    """
    pass


class ResourceNotFound(ClientError):
    """404 Not Found
    """
    pass


class ResourceConflict(ClientError):
    """409 Conflict
    """
    pass


class ResourceGone(ClientError):
    """410 Gone
    """
    pass


class ResourceInvalid(ClientError):
    """422 Invalid
    """
    pass


class ServerError(ConnectionError):
    """5xx Server Error
    """
    pass


class MethodNotAllowed(ClientError):
    """405 Method Not Allowed
    """

    def allowed_methods(self):
        return self.response['Allow']


class ApiError(Exception):
    '''服务器返回错误'''
    
    def __init__(self, code, message=""):
        self.code = code
        self.message = message
    def __str__(self):
        return u"ApiError. code:%d, message:%s" % (self.code, self.message)


class ApiForbiddenAccess(ApiError):
    '''服务器返回403错误'''
    pass
    

class RequestApi(object):

    def __init__(self):
        pass

    @staticmethod
    def _merge_dict(data, *override):
        result = {}
        for current_dict in (data,) + override:
            result.update(current_dict)
        return result

    @staticmethod
    def _handle_response(response, content):
        """Validate HTTP response
        """
        status = response.status_code
        if status in (301, 302, 303, 307):
            raise Redirection(response, content)
        elif 200 <= status <= 299:
            jsonrst = json.loads(content) if content else {}
            return jsonrst
            #if jsonrst['code'] == 0:
            #    return jsonrst
            #if jsonrst['code'] == 403:
            #    raise ApiForbiddenAccess(jsonrst['code'], jsonrst['msg'])
            #elif jsonrst['code'] == 404:
            #    raise ResourceNotFound(response, content)
            #else:
            #    raise ApiError(jsonrst['code'], jsonrst['msg'])
        elif status == 400:
            raise BadRequest(response, content)
        elif status == 401:
            raise UnauthorizedAccess(response, content)
        elif status == 403:
            raise ForbiddenAccess(response, content)
        elif status == 404:
            raise ResourceNotFound(response, content)
        elif status == 405:
            raise MethodNotAllowed(response, content)
        elif status == 409:
            raise ResourceConflict(response, content)
        elif status == 410:
            raise ResourceGone(response, content)
        elif status == 422:
            raise ResourceInvalid(response, content)
        elif 401 <= status <= 499:
            raise ClientError(response, content)
        elif 500 <= status <= 599:
            raise ServerError(response, content)
        else:
            raise ConnectionError(response, content, "Unknown response code: #{response.code}")

    def _headers(self):
        """Default HTTP headers
        """
        return self._merge_dict({
            "content-type": "application/x-www-form-urlencoded",
            "Connection": "Keep-Alive",
        })

    def _http_call(self, url, method, **kwargs):
        """Makes a http call. Logs response information.
        """
        _logger.info("Request[%s]: %s" % (method, url))
        start_time = datetime.datetime.now()
        
        response = requests.request(method,
                                    url,
                                    verify=False,
                                    **kwargs)

        duration = datetime.datetime.now() - start_time
        _logger.info("Response[%d]: %s, Duration: %s.%ss." %
                     (response.status_code, response.reason,
                      duration.seconds, duration.microseconds))

        return self._handle_response(response,
                                     response.content.decode("utf-8"))

    def get_url(self, base_url, action, params={}):
        url = base_url + action #('?' if len(params) else '')
        for key in params:
            #url += '%s=%s&' % (key, params[key])
            url += params[key]
        return url.rstrip('&')

    def call_api(self, url, method="GET", params=None, **kwargs):
        """
        调用API的通用方法，有关SSL证书验证问题请参阅

        http://www.python-requests.org/en/latest/user/advanced/#ssl-cert-verification

        :param action: Method Name，
        :param params: Dictionary,form params for api.
        :param timeout: (optional) Float describing the timeout of the request.
        :return:
        """
        return self._http_call(
            url=url,
            method=method,
            data=params,
            headers=self._headers(),
            **kwargs
        )




                


