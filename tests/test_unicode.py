# -*- coding: utf-8 -*-
from mock import patch, ANY
from six import u
from twilio.rest import TwilioRestClient

client = TwilioRestClient("sid", "token")


@patch("requests.packages.urllib3.connectionpool.HTTPSConnectionPool.urlopen")
def test_double_encoding(urlopen):
    body = u('Chlo\xe9\xf1')

    data = {
        "body": body.encode('utf-8'),
    }

    try:
        client.make_twilio_request("GET", "https://www.example.com", data=data)
    except Exception:
        # We don't return a value here, just want to check the encoding of the
        # request over the wire.
        pass

    urlopen.assert_called_with(method="GET", url="/",
                               # Skip all of the urlopen params we don't care
                               # about...
                               headers=ANY, retries=ANY, redirect=ANY,
                               preload_content=ANY, assert_same_host=ANY,
                               timeout=ANY, decode_content=ANY,

                               # assert that the body is encoded correctly
                               body='body=Chlo%C3%A9%C3%B1')


@patch("requests.packages.urllib3.connectionpool.HTTPSConnectionPool.urlopen")
def test_unicode_sequence_form_value(mock):
    data = {
        "body": [u('\xe5'), u('\xe7')],
    }

    try:
        client.make_twilio_request("POST", "https://www.example.com", data=data)
    except Exception:
        # We don't return a value here, just want to check the encoding of the
        # request over the wire.
        pass

    mock.assert_called_with(
        method="POST", url="/",
        headers=ANY, retries=ANY, redirect=ANY,
        preload_content=ANY, assert_same_host=ANY,
        timeout=ANY, decode_content=ANY,

        body="body=%C3%A5&body=%C3%A7",
    )
