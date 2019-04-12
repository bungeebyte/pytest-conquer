import json
import sys
import time
import zlib

from maketestsgofaster.vendor.httplib2 import Http
from maketestsgofaster import logger


class Client():

    def __init__(self, settings):
        self.api_key = settings.api_key
        self.api_retries = settings.api_retries
        self.api_retry_cap = settings.api_retry_cap
        self.api_timeout = settings.api_timeout
        self.api_urls = settings.api_urls
        self.build_id = settings.build_id
        self.build_node = settings.build_node
        self.user_agent = settings.client_name + '/' + settings.client_version

    def send(self, path, data):
        body = zlib.compress(json.dumps(data).encode('utf8'))
        headers = {
            'Accept': 'application/json',
            'Authorization': self.api_key,
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': self.user_agent,
            'X-Build-Id': self.build_id,
            'X-Build-Node': self.build_node,
        }

        attempts = 0
        result = None
        last_err = None
        wait_before_retry = 0
        while result is None and attempts < self.api_retries + 1:
            url = self.api_urls[0] + path

            if wait_before_retry >= 1:
                logger.debug('retrying in %ss', wait_before_retry)
                time.sleep(min(self.api_retry_cap, wait_before_retry))
            start = time.time()

            try:
                headers['X-Attempt'] = str(attempts)
                response, content = self.request(url, headers, body, max(0.01, self.api_timeout))  # since zero means 'no timeout'
                log_msg = 'status code: ' + str(response.status) + ', request id: ' + str(response.get('x-request-id'))
                if 200 <= response.status < 300:
                    result = json.loads(content.decode('utf-8'))
                    last_err = None
                else:
                    last_err = log_msg
                    if response.status != 404 and 400 <= response.status < 500:  # this means we'll likely not recover anyway
                        break
            except IOError as e:
                self.api_urls.reverse()  # let's try the next API URL because this one seems unreachable
                last_err = e
            finally:
                if last_err:
                    attempts += 1
                    wait_before_retry = 2 ** attempts - (time.time() - start)
                    logger.warning('could not get successful response from server: %s', last_err)

        if last_err:
            sys.exit('server communication error - ' + str(last_err))

        return result

    def request(self, url, headers, body, timeout):
        http = Http(timeout=timeout)
        response, content = http.request(
            url, 'POST', headers=headers, body=body)
        return response, content
