"""
Test that make_request is making correct HTTP requests
"""
import platform

from nose.tools import raises
from mock import patch, Mock, ANY

import twilio
from twilio.rest import TwilioRestException
from twilio.rest import TwilioRestClient
from twilio.rest import Transport

get_headers = {
    "User-Agent": "twilio-python/{version} (Python {python_version})".format(
        version=twilio.__version__,
        python_version=platform.python_version(),
    ),
    "Accept-Charset": "utf-8",
    "Accept": "application/json",
}

post_headers = get_headers.copy()
post_headers["Content-Type"] = "application/x-www-form-urlencoded"


@patch('twilio.rest.requests.request')
def test_make_twilio_request_headers(req):
    url = "http://random/url"
    client = TwilioRestClient("foo", "bar")
    client.make_twilio_request("POST", url)
    req.assert_called_with("POST", "http://random/url.json",
                           headers=post_headers, auth=client.auth,
                           timeout=client.transport.timeout, proxies=ANY,)


@patch('twilio.rest.requests.request')
def test_custom_transport(req):
    url = "http://random/url"
    transport = Transport(retries=7, timeout=3.14, proxies={'http': 'foo'})
    client = TwilioRestClient("foo", "bar", transport)
    client.make_twilio_request("POST", url)
    req.assert_called_with("POST", "http://random/url.json",
                           headers=post_headers,
                           auth=client.auth, timeout=3.14,
                           proxies={'http': 'foo'},)


@raises(TwilioRestException)
@patch('twilio.rest.requests.request')
def test_make_twilio_request_bad_data(mock):
    resp = Mock()
    resp.ok = False
    resp.return_value = "error"
    mock.return_value = resp

    url = "http://random/url"
    client = TwilioRestClient("foo", "bar")
    client.make_twilio_request("POST", url)
    mock.assert_called_with("POST", "http://random/url.json",
                            headers=post_headers,
                            timeout=client.transport.timeout,
                            auth=client.auth)
