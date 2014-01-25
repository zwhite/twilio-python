from datetime import date
import unittest

from mock import Mock, patch

from tools import create_mock_json
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Conferences

DEFAULT = {
    'DateUpdated<': None,
    'DateUpdated>': None,
    'DateUpdated': None,
    'DateCreated<': None,
    'DateCreated>': None,
    'DateCreated': None,
}


class ConferenceTest(unittest.TestCase):

    def setUp(self):
        client = TwilioRestClient("sid", "token")
        self.resource = Conferences("foo", client)
        self.params = DEFAULT.copy()

    def test_list(self):
        self.resource.get_instances = Mock()
        self.resource.list()
        self.resource.get_instances.assert_called_with(self.params)

    def test_list_after(self):
        self.resource.get_instances = Mock()
        self.resource.list(created_after=date(2011, 1, 1))
        self.params["DateCreated>"] = "2011-01-01"
        self.resource.get_instances.assert_called_with(self.params)

    def test_list_on(self):
        self.resource.get_instances = Mock()
        self.resource.list(created=date(2011, 1, 1))
        self.params["DateCreated"] = "2011-01-01"
        self.resource.get_instances.assert_called_with(self.params)

    def test_list_before(self):
        self.resource.get_instances = Mock()
        self.resource.list(created_before=date(2011, 1, 1))
        self.params["DateCreated<"] = "2011-01-01"
        self.resource.get_instances.assert_called_with(self.params)


@patch("twilio.rest.TwilioRestClient.make_twilio_request")
def test_participants(req):
    resp = create_mock_json("tests/resources/participants_instance.json")
    req.return_value = resp
    client = TwilioRestClient("sid", "token")
    client.participants("CF123").get("CA123")
    req.assert_called_with("GET", "https://api.twilio.com/2010-04-01/Accounts/sid/Conferences/CF123/Participants/CA123")
