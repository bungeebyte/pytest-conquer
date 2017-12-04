import json
import time
import zlib

from maketestsgofaster.cloud.vendor.httplib2 import Http
from maketestsgofaster import logger


class Client():

    def __init__(self, settings):
        self.api_key = settings.api_key
        self.api_retries = settings.api_retries
        self.api_timeout = settings.api_timeout
        self.api_url = settings.api_url
        self.build_id = settings.build_id
        self.build_worker = settings.build_worker
        self.user_agent = settings.client_name + '/' + settings.client_version

    def send(self, path, data):
        url = self.api_url + path
        body = zlib.compress(json.dumps(data).encode('utf8'))
        headers = {
            'Accept': 'application/json',
            'Authorization': self.api_key,
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': self.user_agent,
            'X-Build-Id': self.build_id,
            'X-Build-Worker': self.build_worker,
        }

        attempts = 0
        result = None
        last_err = None
        wait_before_retry = 0
        while result is None and attempts < self.api_retries:
            if wait_before_retry >= 1:
                logger.debug('retrying in %ss', wait_before_retry)
                time.sleep(wait_before_retry)
            start = self.__current_time()

            try:
                headers['X-Attempt'] = str(attempts)
                response, content = self.__json_request(url, headers, body, self.api_timeout)
                log_msg = 'status code: ' + str(response.status) + ', request id: ' + str(response.get('x-request-id'))
                if 200 <= response.status < 300:
                    result = json.loads(content.decode('utf-8'))
                    last_err = None
                else:
                    last_err = log_msg
            except IOError as e:
                last_err = e
            finally:
                if last_err:
                    attempts += 1
                    wait_before_retry = max(0, int(self.api_timeout - ((self.__current_time() - start) / 1000)))
                    logger.warning('could not get successful response from server: %s', last_err)

        if last_err:
            raise RuntimeError('server communication error - ' + str(last_err))

        return result

    def __current_time(self):
        return int(round(time.time() * 1000))

    def __json_request(self, url, headers, body, timeout):
        http = Http(timeout=timeout)
        response, content = http.request(
            url, 'POST', headers=headers, body=body)
        return response, content
