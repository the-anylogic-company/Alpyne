import json
import logging
import socket
import urllib.parse
from typing import Tuple, Optional, Union, Any
from urllib.error import HTTPError
from urllib.request import Request

from alpyne.client.utils import AlpyneJSONEncoder
from alpyne.data.model_error import ModelError

RequestResponse = Tuple[int, dict, Optional[Union[dict, list]]]

#LOG_LEVEL = logging.DEBUG

class HttpClient:
    """
    Communication facilitator between Python and the Alpyne app.
    """
    def __init__(self, root_url: str):
        self.root_url = root_url
        self.log = logging.getLogger(__name__)

    def api_request(self, url: str, method: str="GET", body: Any=None) -> RequestResponse:
        """
        :param url: the sub-path (under the root url) to execute a request at
        :param method: the HTTP method
        :param body: data to be included with the request
        :return: the status code, a header dictionary, and the outputs
        :raises ModelError: when encountering an error from the application
        """
        self.log.debug("%s %s: %s", method, url, body)

        url_path = self.root_url + url #urllib.parse.quote(url)
        try:
            request = Request(url_path, method=method, unverifiable=True)
            if body is not None:
                request.data = json.dumps(body, cls=AlpyneJSONEncoder).encode('utf-8')
            request.add_header("Content-Type", "application/json")
            response = urllib.request.urlopen(request, timeout=3)
            if response.getcode() >= 400:  # TODO model errors should warn user and mark episode as halted
                raise ModelError(response.getcode(), response.reason, response.read(), url_path)
        except HTTPError as err:
            # Can either be handled from alpyne or the underlying server
            raise ModelError(err.code, err.reason, err.read(), url_path)
        except socket.timeout as err:
            raise ModelError(err.errno, "timeout|model exception", "see alpyne.log", url_path)

        code = response.getcode()
        headers = response.getheaders()
        output = response.read()
        output = None if not output else json.loads(output)

        self.log.debug("=> %s (%s) %s %s", code, response.reason, headers, output)

        return code, headers, output

    def get(self, url: str) -> RequestResponse:
        return self.api_request(url, method="GET")

    def post(self, url: str, body: Any=None) -> RequestResponse:
        return self.api_request(url, method="POST", body=body)
