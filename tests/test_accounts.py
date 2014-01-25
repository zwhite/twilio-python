import unittest

from mock import patch

from tools import create_mock_json
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Account, Accounts

client = TwilioRestClient('AC123', 'token')
accounts = Accounts('/Accounts', client)


class AccountTest(unittest.TestCase):

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_usage_records_subresource(self, request):
        resp = create_mock_json("tests/resources/usage_records_list.json")
        request.return_value = resp

        account = Account(accounts, 'AC123')
        account.load_subresources()
        records = account.usage_records.list()
        self.assertEquals(len(records), 2)

    @patch("twilio.rest.TwilioRestClient.make_twilio_request")
    def test_usage_triggers_subresource(self, request):
        resp = create_mock_json("tests/resources/usage_triggers_list.json")
        request.return_value = resp

        account = Account(accounts, 'AC123')
        account.load_subresources()
        triggers = account.usage_triggers.list()
        self.assertEquals(len(triggers), 2)
