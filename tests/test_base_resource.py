# -*- coding: utf-8 -*-
import unittest

from mock import Mock
from nose.tools import assert_equal, assert_true
from six import advance_iterator

from twilio.rest import TwilioRestClient
from twilio.rest.resources import Resource
from twilio.rest.resources import ListResource
from twilio.rest.resources import InstanceResource

base_uri = "https://api.twilio.com/2010-04-01"
account_sid = "AC123"
auth = (account_sid, "token")
client = TwilioRestClient(*auth)


def test_resource_init():
    r = Resource(base_uri, client)
    uri = "%s/%s" % (base_uri, r.name)

    assert_equal(r.base_uri, base_uri)
    assert_equal(r.uri, uri)


def test_equivalence():
    p = ListResource(base_uri, client)
    r1 = p.load_instance({"sid": "AC123"})
    r2 = p.load_instance({"sid": "AC123"})
    assert_equal(r1, r2)


class ListResourceTest(unittest.TestCase):

    def setUp(self):
        self.r = ListResource(base_uri, client)

    def testListResourceInit(self):
        uri = "%s/%s" % (base_uri, self.r.name)
        assert_equal(self.r.uri, uri)

    def testKeyValueLower(self):
        assert_equal(self.r.key, self.r.name.lower())

    def testIterNoKey(self):
        self.r.request = Mock()
        self.r.request.return_value = Mock(), {}

        self.assertRaises(StopIteration, advance_iterator, self.r.iter())

    def testRequest(self):
        self.r.request = Mock()
        self.r.request.return_value = Mock(), {self.r.key: [{'sid': 'foo'}]}
        advance_iterator(self.r.iter())
        self.r.request.assert_called_with("GET", "https://api.twilio.com/2010-04-01/Resources", params={})

    def testIterOneItem(self):
        self.r.request = Mock()
        self.r.request.return_value = Mock(), {self.r.key: [{'sid': 'foo'}]}

        items = self.r.iter()
        advance_iterator(items)

        self.assertRaises(StopIteration, advance_iterator, items)

    def testIterNoNextPage(self):
        self.r.request = Mock()
        self.r.request.return_value = Mock(), {self.r.key: []}

        self.assertRaises(StopIteration, advance_iterator, self.r.iter())

    def testKeyValue(self):
        self.r.key = "Hey"
        assert_equal(self.r.key, "Hey")

    def testInstanceLoading(self):
        instance = self.r.load_instance({"sid": "foo"})

        assert_true(isinstance(instance, InstanceResource))
        assert_equal(instance.sid, "foo")

    def testListResourceCreateResponse200(self):
        """We should accept 200 OK in response to a POST creating a resource."""
        self.r.request = Mock()
        return_value = Mock()
        return_value.status_code = 200
        self.r.request.return_value = return_value, {'sid': 'foo'}
        self.r.create_instance({})
        self.r.request.assert_called_with("POST", "https://api.twilio.com/2010-04-01/Resources", data={})

    def testListResourceCreateResponse201(self):
        """We should accept 201 Created in response to a POST creating a resource."""
        self.r.request = Mock()
        return_value = Mock()
        return_value.status_code = 201
        self.r.request.return_value = return_value, {'sid': 'foo'}
        self.r.create_instance({})
        self.r.request.assert_called_with("POST", "https://api.twilio.com/2010-04-01/Resources", data={})


class testInstanceResourceInit(unittest.TestCase):

    def setUp(self):
        client = TwilioRestClient(*auth)
        self.parent = ListResource(base_uri, client)
        self.r = InstanceResource(self.parent, "123")
        self.uri = "%s/%s" % (self.parent.uri, "123")

    def testInit(self):
        assert_equal(self.r.uri, self.uri)

    def testLoad(self):
        self.r.load({"hey": "you"})
        assert_equal(self.r.hey, "you")

    def testLoadWithUri(self):
        self.r.load({"hey": "you", "uri": "foobar"})
        assert_equal(self.r.hey, "you")
        assert_equal(self.r.uri, self.uri)

    def testLoadDateCreated(self):
        self.r.load({"date_created": "Sat, 29 Sep 2012 12:47:54 +0000",
                     "uri": "foobar"})
        try:
            assert_true(hasattr(self.r.date_created, "day"))
            assert_equal(self.r.date_created.day, 29)
        except AttributeError:
            pass

    def testLoadNullDate(self):
        self.r.load({"date_created": None, "uri": "foobar"})
        assert self.r.date_created is None

    def testLoadWithFrom(self):
        self.r.load({"from": "foo"})
        assert_equal(self.r.from_, "foo")

    def testLoadSubresources(self):
        m = Mock()
        self.r.subresources = [m]
        self.r.load_subresources()
        m.assert_called_with(self.r.uri, self.r.client)
