import json
from time import sleep
import logging
import socket
import urllib.parse
from typing import Tuple, Optional, Union, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.parse import (
        urlencode, unquote, urlparse, parse_qsl, ParseResult
    )

from alpyne.client.utils import AlpyneJSONEncoder
from alpyne.data.model_error import ModelError

RequestResponse = Tuple[int, dict, Optional[Union[dict, list]]]

class HttpClient:
    """
    Communication facilitator between Python and the Alpyne app.
    """
    def __init__(self, root_url: str):
        self.root_url = root_url
        self.log = logging.getLogger(__name__)

    @staticmethod
    def add_url_params(url: str, params: dict) -> str:  # https://stackoverflow.com/a/25580545
        """ Add GET params to provided URL being aware of existing.

        :param url: target URL
        :param params: requested params to be added
        :return: updated URL

        >> url = 'https://stackoverflow.com/test'
        >> new_params = {'answers': False, 'data': ['some','values']}
        >> add_url_params(url, new_params)
        'https://stackoverflow.com/test?data=some&data=values&answers=false'
        """
        # Unquoting URL first so we don't lose existing args
        url = unquote(url)
        # Extracting url info
        parsed_url = urlparse(url)
        # Extracting URL arguments from parsed URL
        get_args = parsed_url.query
        # Converting URL arguments to dict
        parsed_get_args = dict(parse_qsl(get_args))
        # Merging URL arguments dict with new params
        parsed_get_args.update(params)

        # Bool and Dict values should be converted to json-friendly values
        # you may throw this part away if you don't like it :)
        parsed_get_args.update(
            {k: json.dumps(v) for k, v in parsed_get_args.items()
             if isinstance(v, (bool, dict))}
        )

        # Converting URL argument to proper query string
        encoded_get_args = urlencode(parsed_get_args, doseq=True)
        # Creating new parsed result object based on provided with new
        # URL arguments. Same thing happens inside urlparse.
        # V- bypass incorrect flagging; may be removable after hard refresh TODO
        # noinspection PyArgumentList
        new_url = ParseResult(
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, encoded_get_args, parsed_url.fragment
        ).geturl()

        return new_url

    def api_request(self, url: str, method: str="GET", params: dict = None, body: Any=None) -> RequestResponse:
        """
        :param url: the sub-path (under the root url) to execute a request at
        :param method: the HTTP method
        :param params: dict containing requested params to be added
        :param body: data to be included with the request
        :return: the status code, a header dictionary, and the outputs
        :raises ModelError: when encountering an error from the application
        """

        url_path = self.root_url + url #urllib.parse.quote(url)
        if params:
            url_path = self.add_url_params(url_path, params)

        self.log.debug("%s %s: %s", method, url_path, body)

        urlErrorCounter = 0
        maxUrlErrors = 10
        success = False
        while not success:
            try:
                request = Request(url_path, method=method, unverifiable=True)
                if body is not None:
                    request.data = json.dumps(body, cls=AlpyneJSONEncoder).encode('utf-8')
                request.add_header("Content-Type", "application/json")

                # when calling `wait_for` increase web request's timeout to 2x the endpoint's timeout
                timeout_val = 10 if params is None else params.get('timeout', 10e3)/1000*2  # convert back to sec from ms
                response = urllib.request.urlopen(request, timeout=timeout_val)
                if response.getcode() >= 400:  # TODO model errors should warn user and mark episode as halted
                    raise ModelError(response.getcode(), response.reason, response.read(), url_path)
                success = True
            except URLError as err:
                self.log.warning(f"[ATTEMPT {urlErrorCounter} / {maxUrlErrors}] ERROR: {err}")
                if urlErrorCounter < maxUrlErrors:
                    urlErrorCounter += 1
                    sleep(0.1)
                else:
                    # Can either be handled from alpyne or the underlying server
                    raise ModelError(err.code, err.reason, err.read(), url_path)
            except HTTPError as err:
                raise ModelError(err.code, err.reason, err.read(), url_path)
            except socket.timeout as err:
                raise ModelError(err.errno, "timeout|model exception", "see alpyne.log", url_path)

        code = response.getcode()
        headers = response.getheaders()
        output = response.read()
        output = None if not output else json.loads(output)

        self.log.debug("=> %s (%s) %s %s", code, response.reason, headers, output)

        return code, headers, output

    def get(self, url: str, params: dict = None) -> RequestResponse:
        return self.api_request(url, method="GET", params=params)

    def post(self, url: str, body: Any = None) -> RequestResponse:
        return self.api_request(url, method="POST", body=body)

    def put(self, url: str, body: Any = None) -> RequestResponse:
        return self.api_request(url, method="PUT", body=body)

    def patch(self, url: str, body: Any = None) -> RequestResponse:
        return self.api_request(url, method="PATCH", body=body)


