import unittest

from mock import patch, Mock, ANY
from nose.tools import assert_equal, assert_true

from tools import create_mock_json
from twilio.rest.resources.imports import json
from twilio.rest import TwilioRestClient, resources

AUTH = ("ACCOUNT_SID", "AUTH_TOKEN")


class RestClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TwilioRestClient("ACCOUNT_SID", "AUTH_TOKEN")

    def test_connect_apps(self):
        assert_true(isinstance(self.client.connect_apps, resources.ConnectApps))

    def test_authorized_apps(self):
        assert_true(isinstance(self.client.authorized_connect_apps,
                    resources.AuthorizedConnectApps))

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_conferences(self, mock):
        mock.return_value = Mock()
        mock.return_value.ok = True
        mock.return_value.content = '{"conferences": []}'
        self.client.conferences.list()

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_members(self, mock):
        resp = create_mock_json("tests/resources/members_list.json")
        mock.return_value = resp
        self.client.members("QU123").list()
        uri = "https://api.twilio.com/2010-04-01/Accounts/ACCOUNT_SID/Queues/QU123/Members"
        mock.assert_called_with("GET", uri, params={})


class RestClientMembersTest(unittest.TestCase):
    def setUp(self):
        self.client = TwilioRestClient("ACCOUNT_SID", "AUTH_TOKEN")

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_members(self, mock_request):
        resp = create_mock_json("tests/resources/members_list.json")
        mock_request.return_value = resp
        self.client.members("QU123").list()
        uri = "https://api.twilio.com/2010-04-01/Accounts/ACCOUNT_SID/Queues/QU123/Members"
        mock_request.assert_called_with("GET", uri, params={})

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_arbitrary_member(self, mock_request):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = json.dumps({"short_codes": []})
        mock_request.return_value = mock_response
        assert_equal([], self.client.sms.short_codes.list())
        mock_request.assert_called_once_with("GET", ANY, params={})
