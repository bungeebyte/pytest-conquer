import json
import sys
import time
import zlib
import datetime
import uuid
import wsgiref.handlers
from time import mktime

from testandconquer.vendor.httplib2 import Http, HttpLib2Error
from testandconquer import logger


class Client():

    def __init__(self, settings):
        self.api_key = settings.api_key
        self.api_retries = settings.api_retries
        self.api_retry_cap = settings.api_retry_cap
        self.api_timeout = settings.api_timeout
        self.api_urls = [settings.api_url, settings.api_url_fallback]
        self.build_id = settings.build_id or 'unknown'  # might not be initialized yet
        self.build_node = settings.build_node or 'unknown'  # might not be initialized yet
        self.user_agent = settings.client_name + '/' + settings.client_version

    def get(self, path):
        return self._request(path, 'GET', None)

    def put(self, path, data):
        return self._request(path, 'PUT', data)

    def post(self, path, data):
        return self._request(path, 'POST', data)

    def _request(self, path, method, data):
        attempts = 0
        result = None
        last_err = None
        wait_before_retry = 0
        headers, body = self._prepare_request(data)
        while result is None and attempts < self.api_retries + 1:
            url = self.api_urls[0] + path

            if wait_before_retry >= 1:
                logger.debug('retrying in %ss', wait_before_retry)
                time.sleep(min(self.api_retry_cap, wait_before_retry))
            start = time.time()

            status_code = 0
            try:
                headers['X-Attempt'] = str(attempts)
                response, content = self._execute_request(method, url, headers, body, max(0.01, self.api_timeout))  # since zero means 'no timeout'
                result, last_err = self._parse_reponse(response, content)
                status_code = response.status
                if status_code != 404 and 400 <= status_code < 500:  # this means we'll likely not recover anyway
                    attempts = self.api_retries + 1
            except (HttpLib2Error, IOError) as e:
                self.api_urls.reverse()  # let's try the next API URL because this one seems unreachable
                last_err = e
            finally:
                if last_err:
                    attempts += 1
                    wait_before_retry = 2 ** attempts - (time.time() - start)
                    logger.warning('could not get successful response from server [status=%s] [request-id=%s]: %s', status_code, headers['X-Request-Id'], last_err)

        if last_err:
            sys.exit('EXIT: server communication error')

        return result

    def _prepare_request(self, data):
        headers = {
            'Accept': 'application/json',
            'Authorization': str(self.api_key),
            'Date': wsgiref.handlers.format_date_time(mktime(datetime.datetime.now().timetuple())),
            'User-Agent': str(self.user_agent),
            'X-Build-Id': str(self.build_id),
            'X-Build-Node': str(self.build_node),
            'X-Request-Id': str(uuid.uuid4()),
        }

        if data:
            body = zlib.compress(json.dumps(data).encode('utf8'))
            headers['Content-Encoding'] = 'gzip'
            headers['Content-Type'] = 'application/json; charset=UTF-8'
        else:
            body = None

        return headers, body

    def _execute_request(self, method, url, headers, body, timeout):
        http = Http(timeout=timeout)
        return http.request(url, method, headers=headers, body=body)

    def _parse_reponse(self, response, content):
        json_resp = None
        try:
            json_resp = json.loads(content.decode('utf-8')) if content else {}
        except ValueError:
            pass
        if not isinstance(json_resp, dict):
            return None, 'invalid JSON response'

        if 200 <= response.status < 300:
            return json_resp, None

        err_msg = (json_resp.get('error') if json_resp else None) or ('Server Error' if response.status >= 500 else 'Client Error')
        return None, err_msg
