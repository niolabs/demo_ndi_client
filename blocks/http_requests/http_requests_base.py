import json
import requests
from enum import Enum

from nio.block.base import Block
from nio.block.mixins import Retry, EnrichSignals
from nio.properties import (Property, IntProperty, BoolProperty,
                            PropertyHolder, ListProperty, ObjectProperty,
                            SelectProperty, StringProperty, VersionProperty)
from nio.util.discovery import not_discoverable


class Header(PropertyHolder):
    header = Property(title='Header', allow_none=True)
    value = Property(title='Value', allow_none=True)


class BasicAuthCreds(PropertyHolder):
    username = StringProperty(title='Username', allow_none=True)
    password = StringProperty(title='Password', allow_none=True)


class HTTPMethod(Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'
    HEAD = 'head'
    OPTIONS = 'options'


@not_discoverable
class HTTPRequestsBase(Retry, EnrichSignals, Block):

    """ A base for Blocks that makes HTTP Requests.

    Properties:
        url (str): URL to make request to.
        basic_auth_creds (obj): Basic Authentication credentials.
        http_method (select): HTTP method (ex. GET, POST,
            PUT, DELETE, etc).
    """
    version = VersionProperty('0.1.0')
    url = Property(title='URL Target',
                   default="http://127.0.0.1:8181")
    basic_auth_creds = ObjectProperty(BasicAuthCreds,
                                      title='Credentials (BasicAuth)',
                                      default=BasicAuthCreds())
    http_method = SelectProperty(
        HTTPMethod,
        default=HTTPMethod.GET,
        title='HTTP Method'
    )
    headers = ListProperty(Header, title="Headers", default=[])
    require_json = BoolProperty(title="Require JSON Response", default=False)
    verify = BoolProperty(
        title="Verify host's SSL certificate", default=True, visible=False
    )
    timeout = IntProperty(title='Request Timeout', default=0, allow_none=True)

    def process_signals(self, signals):
        new_signals = []
        for signal in signals:
            new_sigs = self._make_request(signal)
            if new_sigs:
                new_signals.extend(new_sigs)
        if new_signals:
            self.notify_signals(new_signals)

    def _make_request(self, signal):
        try:
            url = self.url(signal)
        except Exception as e:
            self.logger.warning(
                "Failed to evaluate url {} for incoming signal {}: {}"
                .format(self.url.value, signal.to_dict(), e)
            )
            return
        timeout = self.timeout(signal) if self.timeout(signal) else None
        auth = self._create_auth()
        payload = self._create_payload(signal)
        headers = self._create_headers(signal)

        try:
            r = self.execute_with_retry(self._execute_request,
                                        url, auth, payload, headers, timeout)
        except:
            # out of retries for this signal
            return

        if 200 <= r.status_code < 300:
            return self._process_response(r, signal)
        else:
            self.logger.warning(
                "{} request to {} returned with response code: {}".format(
                    self.http_method(),
                    url,
                    r.status_code
                )
            )
            return self._process_response(r, signal)

    def _execute_request(self, url, auth, data, headers, timeout):
        method = getattr(requests, self.http_method().value)

        self.logger.debug("Executing {} request to {} with data: {}"
                          .format(self.http_method(), url,
                                  {"auth": auth, "data": data,
                                   "headers": headers, "timeout": timeout}))

        return method(url, auth=auth, data=data, headers=headers,
                      verify=self.verify(), timeout=timeout)

    def _process_response(self, response, signal):
        result = []
        try:
            data = response.json()

            # if the response is a dictionary, build a signal
            if isinstance(data, dict):
                result = [self.get_output_signal(data, signal)]

            # if the response is a list, build a signal for each element
            elif isinstance(data, list):
                sigs = []
                for s in data:
                    sigs.append(
                        self.get_output_signal(s, signal))
                if sigs:
                    result = sigs

            # otherwise, no dice on parsing the response body
            else:
                raise ValueError("Response body could not be parsed into "
                                     "Signal(s): {}".format(data))
        except ValueError:
            if not self.require_json():
                result = [self.get_output_signal(
                    {'raw': response.text}, signal)]
            else:
                self.logger.warning(
                    "Request was successful, but response was not "
                    "valid JSON. No response signal was created."
                )
                result = [signal]
        except Exception as e:
            self.logger.warning(
                "Request was successful but "
                "failed to create response signal: {}".format(e)
            )
            result = [signal]
        finally:
            # Add the rest of the Response information to the signal
            for sig in result:
                try:
                    sig._resp = response.__dict__
                except:
                    self.logger.warning("Response failed to save to signal")

            self.logger.debug("{} request to {} returned with response code: "
                              "{}. Response: {}"
                              .format(self.http_method(),
                                      self.url(signal),
                                      response.status_code,
                                      response.__dict__))
            return result

    def _create_auth(self):
        if self.basic_auth_creds().username():
            return requests.auth.HTTPBasicAuth(
                self.basic_auth_creds().username(),
                self.basic_auth_creds().password()
            )

    def _create_payload(self, signal):
        return json.dumps(signal.to_dict())

    def _create_headers(self, signal):
        headers = {}
        for header in self.headers():
            header_header = header.header(signal)
            header_value = header.value(signal)
            if header_header and header_value:
                headers[header_header] = header_value
        return headers
