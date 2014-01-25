import unittest

from mock import Mock
from nose.tools import assert_equal, assert_true

from twilio import TwilioException
from twilio.rest import TwilioRestClient
from twilio.rest.resources import AvailablePhoneNumber
from twilio.rest.resources import AvailablePhoneNumbers
from twilio.rest.resources import PhoneNumbers

BASE = "https://api.twilio.com"


class AvailablePhoneNumberTest(unittest.TestCase):

    def setUp(self):
        self.parent = Mock()
        self.instance = AvailablePhoneNumber(self.parent)

    def test_init(self):
        assert_equal(self.instance.name, "")

    def test_purchase(self):
        self.instance.phone_number = "+123"
        self.instance.purchase(voice_url="http://www.google.com")

        self.parent.purchase.assert_called_with(
            voice_url="http://www.google.com",
            phone_number="+123")


class AvailablePhoneNumbersTest(unittest.TestCase):

    def setUp(self):
        client = TwilioRestClient("user", "pass")
        self.resource = AvailablePhoneNumbers(BASE, client, Mock())

    def test_get(self):
        self.assertRaises(TwilioException, self.resource.get, "PN123")

    def test_list(self):
        request = Mock()
        request.return_value = (Mock(), {"available_phone_numbers": []})
        self.resource.request = request

        self.resource.list()

        uri = BASE + "/AvailablePhoneNumbers/US/Local"
        request.assert_called_with("GET", uri, params={})

    def test_load_instance(self):
        instance = self.resource.load_instance({"hey": "you"})
        assert_true(isinstance(instance.parent, Mock))
        assert_equal(instance.hey, "you")

    def test_purchase_status_callback(self):
        request = Mock()
        request.return_value = (Mock(), {"available_phone_numbers": []})
        self.resource.request = request

        self.resource.list()

        uri = BASE + "/AvailablePhoneNumbers/US/Local"
        request.assert_called_with("GET", uri, params={})

    def test_mobile(self):
        request = Mock()
        request.return_value = (Mock(), {"available_phone_numbers": []})
        self.resource.request = request

        self.resource.list(type='mobile', country='GB')

        uri = BASE + "/AvailablePhoneNumbers/GB/Mobile"
        request.assert_called_with("GET", uri, params={})


class PhoneNumbersTest(unittest.TestCase):

    def setUp(self):
        client = TwilioRestClient("user", "pass")
        self.resource = PhoneNumbers(BASE, client)

    def test_reference(self):
        assert_equal(self.resource.available_phone_numbers.phone_numbers,
                     self.resource)

    def test_purchase_status_callback(self):
        request = Mock()
        response = Mock()
        response.status_code = 201
        request.return_value = (response, {"sid": ""})
        self.resource.request = request

        self.resource.purchase(area_code="530", status_callback_url="http://",
                               status_callback_method="POST")

        uri = BASE + "/IncomingPhoneNumbers"

        data = {
            "AreaCode": "530",
            "StatusCallback": "http://",
            "StatusCallbackMethod": "POST",
            }

        request.assert_called_with("POST", uri, data=data)
